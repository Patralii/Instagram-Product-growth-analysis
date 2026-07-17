-- QUESTION WE'RE ANSWERING:
--   Did treatment users spend more time in the app per day than control
--   users -- the experiment's primary metric?
--
-- WHY IT MATTERS:
--   This is the metric the whole experiment was powered and pre-registered
--   to detect. Everything else (engagement rate, Stories effects,
--   guardrails) is secondary to whether this number moved, and by how
--   much, with what confidence.
--
-- APPROACH:
--   Aggregate session_duration_sec per user per day, then average across
--   users within each variant. STDDEV is pulled alongside the mean because
--   the confidence interval and significance test (computed downstream,
--   not in raw SQL) need both. Always filter out SRM-affected rows first --
--   see 03_srm_bucket_check.sql.
-- ============================================================================

WITH daily_time AS (
    SELECT
        s.user_id,
        ea.variant,
        s.session_start,
        s.session_duration_sec / 60.0 AS minutes
    FROM sessions s
    JOIN experiment_assignments ea ON s.user_id = ea.user_id
    WHERE ea.affected_by_srm_bug = FALSE
)
SELECT
    variant,
    COUNT(DISTINCT user_id)          AS n_users,
    ROUND(AVG(minutes), 2)            AS avg_minutes_per_session_day,
    ROUND(
        SQRT(AVG(minutes * minutes) - AVG(minutes) * AVG(minutes)),
        2
    ) AS stddev_minutes  -- population stddev, computed manually for portability across engines
FROM daily_time
GROUP BY variant;
