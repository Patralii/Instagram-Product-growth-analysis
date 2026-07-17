-- QUESTION WE'RE ANSWERING:
--   Did the 50/50 random assignment actually land at 50/50? And does
--   excluding the rows flagged by the bucketing-bug investigation fix it?
--
-- WHY IT MATTERS:
--   A Sample Ratio Mismatch (SRM) means randomization broke -- treatment
--   and control are no longer comparable groups, and every other metric
--   in the project becomes untrustworthy until this is checked and fixed.
--   This is the validity gate that has to pass BEFORE any of the results
--   queries (04 onward) are worth running.
--
-- APPROACH:
--   Run this query twice in practice: once including all rows, once with
--   affected_by_srm_bug = FALSE. The output (n_users per variant) feeds a
--   chi-square goodness-of-fit test against the expected 50/50 split,
--   computed in whatever analysis tool sits downstream of SQL (Python,
--   Tableau calculated field, or by hand). SQL's job here is just to
--   produce clean counts -- the test itself isn't expressible in SQL.
-- ============================================================================

-- Run 1: all assignments, bug included -- this is the version that fails the
-- chi-square check (treatment and control counts skew apart).
SELECT
    variant,
    COUNT(DISTINCT user_id) AS n_users
FROM experiment_assignments
GROUP BY variant;

-- Run 2: excluding the rows affected by the bucketing bug -- this is the
-- version that should pass (counts close to even).
SELECT
    variant,
    COUNT(DISTINCT user_id) AS n_users
FROM experiment_assignments
WHERE affected_by_srm_bug = FALSE
GROUP BY variant;

-- Supplementary: what % of traffic was affected, broken out by platform and
-- ATT status -- this is what actually pinpoints the bug (a fallback hashing
-- path that disproportionately hit ATT-denied iOS users).
SELECT
    platform,
    att_status,
    COUNT(*) AS n_users,
    ROUND(100.0 * AVG(CASE WHEN affected_by_srm_bug THEN 1 ELSE 0 END), 1) AS pct_affected
FROM experiment_assignments
GROUP BY platform, att_status
ORDER BY pct_affected DESC;
