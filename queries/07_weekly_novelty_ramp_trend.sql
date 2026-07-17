-- QUESTION WE'RE ANSWERING:
--   Does the Reels-engagement lift and the Stories-posting lift behave the
--   same way over the 4-week test window -- or does one decay (a novelty
--   effect) while the other builds (a habit forming)?
--
-- WHY IT MATTERS:
--   A lift measured only at the end of a test can't tell you whether it's
--   durable. Breaking both metrics out by week is what reveals that Reels
--   engagement decays in a classic novelty pattern, while Stories posting
--   does the opposite -- which is the evidence that the posting effect is
--   a real behavior change worth recommending action on, not a curiosity
--   spike about to vanish.
--
-- APPROACH:
--   Bucket events into week_number (0-3) relative to the test start, then
--   compute each metric's rate per week, per variant. Two separate
--   queries below since they pull from two different tables.
-- ============================================================================

-- Weekly Reels engagement rate: engagements / impressions, by week and variant
SELECT
    CAST((julianday(fi.served_at) - julianday('2026-04-01')) / 7 AS INT) AS week_number,
    ea.variant,
    COUNT(DISTINCT ree.event_id) * 1.0 / COUNT(DISTINCT fi.impression_id) AS engagement_rate
FROM feed_impressions fi
JOIN experiment_assignments ea ON fi.user_id = ea.user_id
LEFT JOIN reel_engagement_events ree ON fi.impression_id = ree.impression_id
WHERE ea.affected_by_srm_bug = FALSE
GROUP BY week_number, ea.variant
ORDER BY week_number, ea.variant;

-- Weekly Stories posting rate: % of users posting, by week and variant
SELECT
    CAST((julianday(se.event_at) - julianday('2026-04-01')) / 7 AS INT) AS week_number,
    ea.variant,
    COUNT(DISTINCT CASE WHEN se.event_type = 'post' THEN se.user_id END) * 1.0
        / COUNT(DISTINCT ea.user_id) AS posting_rate
FROM experiment_assignments ea
LEFT JOIN stories_events se ON ea.user_id = se.user_id
WHERE ea.affected_by_srm_bug = FALSE
GROUP BY week_number, ea.variant
ORDER BY week_number, ea.variant;

-- NOTE: julianday() is SQLite-specific (used for local testing against this
-- project's sample data). In PostgreSQL, replace the week_number expression
-- with: EXTRACT(DAY FROM served_at - DATE '2026-04-01')::INT / 7
