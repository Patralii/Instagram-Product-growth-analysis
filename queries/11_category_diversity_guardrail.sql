-- QUESTION WE'RE ANSWERING:
--   Do users in the clustered/treatment version of Explore end up seeing
--   FEWER distinct content categories per week than users in the flat/
--   control version -- the "filter bubble" risk?
--
-- WHY IT MATTERS:
--   Grouping content by interest could backfire by narrowing what people
--   are exposed to overall, even if they click more within their own
--   cluster. This is the guardrail that catches that risk directly. The
--   serendipity-injection mechanism (roughly 1-in-10 impressions from
--   outside a user's home category) was designed specifically to keep
--   this number from collapsing -- this query is how we check whether
--   that mitigation is actually working, not just assumed to be working.
--
-- APPROACH:
--   COUNT(DISTINCT cluster_category) per user, then average across users
--   within each variant. A meaningfully lower number in treatment would
--   be a real finding worth flagging, not waving away.
-- ============================================================================

WITH per_user_diversity AS (
    SELECT
        user_id,
        variant,
        COUNT(DISTINCT cluster_category) AS distinct_categories_seen
    FROM explore_impressions
    GROUP BY user_id, variant
)
SELECT
    variant,
    ROUND(AVG(distinct_categories_seen), 2) AS avg_distinct_categories_per_user,
    MIN(distinct_categories_seen)            AS min_categories,
    MAX(distinct_categories_seen)            AS max_categories,
    COUNT(*)                                 AS n_users
FROM per_user_diversity
GROUP BY variant
ORDER BY variant;
