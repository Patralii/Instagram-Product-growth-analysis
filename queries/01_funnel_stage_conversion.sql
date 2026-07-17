
-- QUESTION WE'RE ANSWERING:
--   How many users reach each stage of Signup -> First Post -> First
--   Follow -> DAU, and what % of the original signup cohort does each
--   stage represent?
--
-- WHY IT MATTERS:
--   This is the single query that produces the project's headline number
--   (Signup -> First Post drop-off of ~64%). Everything downstream -- the
--   business case for testing Reels, the targeting logic in the
--   recommendation -- depends on first establishing where the funnel
--   actually leaks. Get this wrong and the rest of the narrative has no
--   foundation.
--
-- APPROACH:
--   funnel_events is a tidy/long table -- one row per user per stage
--   reached. Counting DISTINCT user_id per stage, then dividing by the
--   signup count, gives "% of original cohort still present" at each
--   stage -- which is the right denominator for a funnel (not the
--   previous stage's count, which would hide how much has been lost
--   overall).
-- ============================================================================

WITH stage_counts AS (
    SELECT
        stage,
        COUNT(DISTINCT user_id) AS n_users
    FROM funnel_events
    GROUP BY stage
),
-- WHAT: pin down stage order explicitly, since funnel stages have a
-- defined sequence that doesn't sort alphabetically.
-- WHY: window functions below (FIRST_VALUE, LAG) need a reliable ORDER BY.
ordered AS (
    SELECT
        stage,
        n_users,
        CASE stage
            WHEN 'signup'       THEN 1
            WHEN 'first_post'   THEN 2
            WHEN 'first_follow' THEN 3
            WHEN 'dau'          THEN 4
        END AS stage_order
    FROM stage_counts
)
SELECT
    stage,
    n_users,
    ROUND(100.0 * n_users / FIRST_VALUE(n_users) OVER (ORDER BY stage_order), 1)
        AS pct_of_signups,
    ROUND(100.0 * (1 - n_users * 1.0 / LAG(n_users) OVER (ORDER BY stage_order)), 1)
        AS stage_drop_off_pct
FROM ordered
ORDER BY stage_order;
