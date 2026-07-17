-- QUESTION WE'RE ANSWERING:
--   Of the content people actually clicked on, what share belonged to
--   new/small creators (fewer than 100 followers, or joined in the last
--   30 days) -- and is that share higher in the clustered/treatment
--   version of Explore than in the flat/control version?
--
-- WHY IT MATTERS:
--   This is the metric that actually answers the equity question Part 3
--   exists to test. A CTR win (query 09) on its own doesn't tell you
--   WHO is benefiting -- it's entirely possible to raise clicks while
--   still showing only the same already-popular accounts, just grouped
--   under topic headers. This query checks whether the new-creator
--   visibility boost mechanism is doing what it was designed to do: give
--   Part 2's newly-created creators (the never-posted-before users who
--   started posting) an actual chance to be seen.
--
-- APPROACH:
--   Join impressions to creator_profile to get is_new_creator, restrict
--   to clicked rows only (we care about what got engaged with, not just
--   shown), and compute the % belonging to new/small creators per variant.
-- ============================================================================

SELECT
    ei.variant,
    COUNT(*)                                                    AS n_clicks,
    SUM(CASE WHEN cp.is_new_creator THEN 1 ELSE 0 END)           AS n_clicks_new_creator,
    ROUND(100.0 * AVG(CASE WHEN cp.is_new_creator THEN 1 ELSE 0 END), 1)
        AS pct_clicks_to_new_creators
FROM explore_impressions ei
JOIN creator_profile cp ON ei.creator_id = cp.creator_id
WHERE ei.clicked = TRUE
GROUP BY ei.variant
ORDER BY ei.variant;
