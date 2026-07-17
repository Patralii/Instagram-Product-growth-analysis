-- QUESTION WE'RE ANSWERING:
--   Among users who DO reach each stage, how many days does it typically
--   take them, measured from signup?
--
-- WHY IT MATTERS:
--   Conversion rate tells you how many people make it. Time-to-convert
--   tells you about urgency -- it defines the window during which an
--   intervention (a prompt, an email, a UI nudge) could realistically
--   still reach someone before they've effectively already decided not to
--   convert. A median of 2.3 days to First Post means a "come back and
--   post!" campaign sent on day 10 is too late for most people who were
--   ever going to convert quickly.
--
-- APPROACH:
--   PERCENTILE_CONT gives the median (and could give any other percentile)
--   directly, rather than approximating with AVG, which is sensitive to a
--   long right tail of slow converters. This is real PostgreSQL syntax
--   (this project's target engine, per the tech stack) -- it is NOT
--   supported by SQLite, which has no percentile function at all.
-- ============================================================================

SELECT
    stage,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY days_since_signup) AS median_days,
    ROUND(AVG(days_since_signup), 1) AS mean_days,
    COUNT(*) AS n_users
FROM funnel_events
WHERE stage != 'signup'  -- signup is day 0 by definition, not informative here
GROUP BY stage
ORDER BY
    CASE stage
        WHEN 'first_post'   THEN 1
        WHEN 'first_follow' THEN 2
        WHEN 'dau'          THEN 3
    END;

-- ----------------------------------------------------------------------------
-- SQLite-compatible equivalent (for local testing against this project's
-- sample data only -- PostgreSQL's PERCENTILE_CONT above is the real,
-- intended version). SQLite has no percentile function, so the median is
-- approximated here via a windowed row-count midpoint instead.
-- ----------------------------------------------------------------------------
WITH ranked AS (
    SELECT
        stage,
        days_since_signup,
        ROW_NUMBER() OVER (PARTITION BY stage ORDER BY days_since_signup) AS rn,
        COUNT(*) OVER (PARTITION BY stage) AS cnt
    FROM funnel_events
    WHERE stage != 'signup'
)
SELECT
    stage,
    AVG(days_since_signup) AS median_days_approx,  -- avg of the 1-2 middle-ranked rows
    COUNT(*) AS n_in_median_window
FROM ranked
WHERE rn IN (CAST((cnt + 1) / 2 AS INT), CAST((cnt + 2) / 2 AS INT))
GROUP BY stage;
