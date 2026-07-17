-- QUESTION WE'RE ANSWERING:
--   Is the Stories-posting lift spread evenly across all experiment users,
--   or is it concentrated in the segment who hadn't posted before the
--   test started -- the exact group the Part 1 funnel flagged as stuck?
--
-- WHY IT MATTERS:
--   This is the query that connects Part 1 and Part 2. A population-level
--   average (+18.3% posting lift) can hide very different stories for
--   different segments. If the lift is concentrated in never-posted
--   users, that changes the recommendation from "ship broadly" to "ship
--   broadly, but specifically target the activation nudge at this
--   segment" -- a much more useful, defensible answer than the average
--   alone.
--
-- APPROACH:
--   had_posted_pre_test (set at assignment time, before the test started)
--   is the segment flag. Cross it with variant to get a 2x2 cut, then
--   compare posting rate within each combination.
-- ============================================================================

SELECT
    ea.variant,
    ea.had_posted_pre_test,
    COUNT(DISTINCT ea.user_id) AS n_users,
    COUNT(DISTINCT CASE WHEN se.event_type = 'post' THEN se.user_id END) AS n_users_posted,
    ROUND(
        100.0 * COUNT(DISTINCT CASE WHEN se.event_type = 'post' THEN se.user_id END)
            / COUNT(DISTINCT ea.user_id),
        2
    ) AS posting_rate_pct
FROM experiment_assignments ea
LEFT JOIN stories_events se
    ON ea.user_id = se.user_id
WHERE ea.affected_by_srm_bug = FALSE
GROUP BY ea.variant, ea.had_posted_pre_test
ORDER BY ea.had_posted_pre_test, ea.variant;
