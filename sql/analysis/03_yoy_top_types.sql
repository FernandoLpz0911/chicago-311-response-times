-- Is the city getting faster or slower? Median response hours by year for the 10 busiest
-- request types. 2026 is a partial year, so seasonal types (snow, tree trimming) can skew it.
WITH top_types AS (
    SELECT sr_type
    FROM mart.v_requests_clean
    GROUP BY sr_type
    ORDER BY count(*) DESC
    LIMIT 10
)
SELECT
    c.sr_type,
    count(*) AS requests,
    round((percentile_cont(0.5) WITHIN GROUP (ORDER BY c.response_hours)
        FILTER (WHERE extract(year FROM c.created_date) = 2023))::numeric, 1) AS median_2023,
    round((percentile_cont(0.5) WITHIN GROUP (ORDER BY c.response_hours)
        FILTER (WHERE extract(year FROM c.created_date) = 2024))::numeric, 1) AS median_2024,
    round((percentile_cont(0.5) WITHIN GROUP (ORDER BY c.response_hours)
        FILTER (WHERE extract(year FROM c.created_date) = 2025))::numeric, 1) AS median_2025,
    round((percentile_cont(0.5) WITHIN GROUP (ORDER BY c.response_hours)
        FILTER (WHERE extract(year FROM c.created_date) = 2026))::numeric, 1) AS median_2026
FROM mart.v_requests_clean AS c
JOIN top_types AS t USING (sr_type)
GROUP BY c.sr_type
ORDER BY requests DESC;
