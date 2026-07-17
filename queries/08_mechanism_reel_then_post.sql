-- QUESTION WE'RE ANSWERING:
--   When someone posts a Story, how often did they watch a Reel
--   immediately before it, in the same session -- and does this happen
--   more in treatment than control?
--
-- WHY IT MATTERS:
--   A correlation (Reels exposure went up, Stories posting went up) isn't
--   the same as a mechanism. This query is the closest thing to direct
--   evidence for the "inspiration" story: if treatment posts are
--   systematically preceded by a Reel watch far more often than control
--   posts are, that's a same-session behavioral sequence pointing at
--   cause, not just two numbers that happened to move together.
--
-- APPROACH:
--   preceded_by_reel is set at generation/event-logging time (a session-
--   level join between Reels and Stories activity, already resolved
--   upstream into a boolean flag on each post event). This query just
--   aggregates that flag by variant.
-- ============================================================================

SELECT
    ea.variant,
    COUNT(*) AS n_posts,
    SUM(CASE WHEN se.preceded_by_reel THEN 1 ELSE 0 END) AS n_posts_preceded_by_reel,
    ROUND(100.0 * AVG(CASE WHEN se.preceded_by_reel THEN 1 ELSE 0 END), 1)
        AS pct_posts_preceded_by_reel
FROM stories_events se
JOIN experiment_assignments ea ON se.user_id = ea.user_id
WHERE se.event_type = 'post'
  AND ea.affected_by_srm_bug = FALSE
GROUP BY ea.variant;
