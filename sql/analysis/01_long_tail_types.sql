-- Which services help most people quickly but leave some waiting far longer?
-- Long tail = the gap between the 90th percentile and the median response time.
-- Only types with at least 1,000 completed requests, so the percentiles are stable.
WITH per_type AS (
    SELECT
        sr_type,
        count(response_hours) AS completed,
        percentile_cont(0.5) WITHIN GROUP (ORDER BY response_hours) AS median_hours,
        percentile_cont(0.9) WITHIN GROUP (ORDER BY response_hours) AS p90_hours
    FROM mart.v_requests_clean
    GROUP BY sr_type
    HAVING count(response_hours) >= 1000
)
SELECT
    sr_type,
    completed,
    round(median_hours::numeric, 1) AS median_hours,
    round(p90_hours::numeric, 1) AS p90_hours,
    round((p90_hours / NULLIF(median_hours, 0))::numeric, 1) AS p90_to_median
FROM per_type
ORDER BY p90_hours - median_hours DESC
LIMIT 15;
