-- QUESTION WE'RE ANSWERING:
--   Did the Interest-Based Clusters version of Explore/Search (treatment)
--   get a higher click-through rate than the flat, algorithmic version
--   (control)?
--
-- WHY IT MATTERS:
--   This is Part 3's primary metric -- the most basic test of "did
--   grouping content by topic help people find things they actually
--   wanted to click." It's the metric every other Part 3 query (equity,
--   diversity) needs to be read alongside, not instead of -- a CTR win
--   that comes from burying new creators even further wouldn't be a real
--   win for the business question this test was built to answer.
--
-- APPROACH:
--   Simple rate: clicks / impressions, by variant. clicked is stored as a
--   boolean per impression row, so AVG() of that column directly gives
--   the click-through rate.
-- ============================================================================

SELECT
    variant,
    COUNT(*)                                AS n_impressions,
    SUM(CASE WHEN clicked THEN 1 ELSE 0 END) AS n_clicks,
    ROUND(100.0 * AVG(CASE WHEN clicked THEN 1 ELSE 0 END), 2) AS ctr_pct
FROM explore_impressions
GROUP BY variant
ORDER BY variant;
