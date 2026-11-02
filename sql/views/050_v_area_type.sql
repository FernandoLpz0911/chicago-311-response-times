-- Response time by community area within each request type. Comparing areas across all
-- types at once would mostly reflect which kinds of requests each area files.
CREATE OR REPLACE VIEW mart.v_area_type AS
SELECT
    c.community_area,
    a.name AS area_name,
    c.sr_type,
    count(*) AS requests,
    count(c.response_hours) AS completed,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY c.response_hours) AS median_hours,
    percentile_cont(0.9) WITHIN GROUP (ORDER BY c.response_hours) AS p90_hours
FROM mart.v_requests_clean AS c
LEFT JOIN ref.community_areas AS a ON a.area_number = c.community_area
WHERE c.community_area IS NOT NULL
GROUP BY c.community_area, a.name, c.sr_type;
