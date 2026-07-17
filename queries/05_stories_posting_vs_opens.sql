-- QUESTION WE'RE ANSWERING:
--   Did treatment users open (consume) Stories less, as the cannibalization
--   assumption predicted -- and separately, did they POST (create) Stories
--   more or less?
--
-- WHY IT MATTERS:
--   This is the query that surfaces the project's headline twist. The
--   team's working assumption was "more Reels will cannibalize Stories."
--   Treating "Stories opens" and "Stories posts" as two separate metrics
--   -- rather than one blended "Stories activity" number -- is what reveals
--   that consumption didn't drop AND creation rose sharply. Collapsing
--   them into one metric would have hidden the finding entirely.
--
-- APPROACH:
--   % of users who opened/posted at least once, by variant and event
--   type, over the full test window. Using % of users (not raw event
--   counts) avoids a handful of power-users skewing the picture.
-- ============================================================================

SELECT
    ea.variant,
    se.event_type,
    COUNT(DISTINCT se.user_id)                                   AS n_users_with_event,
    COUNT(DISTINCT ea.user_id)                                   AS n_users_total,
    ROUND(100.0 * COUNT(DISTINCT se.user_id) / COUNT(DISTINCT ea.user_id), 2)
        AS pct_of_users
FROM experiment_assignments ea
LEFT JOIN stories_events se
    ON ea.user_id = se.user_id
WHERE ea.affected_by_srm_bug = FALSE
GROUP BY ea.variant, se.event_type
ORDER BY ea.variant, se.event_type;
