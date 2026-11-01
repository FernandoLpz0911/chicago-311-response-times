-- Response time by intake channel (phone, web, app, ...) within each request type.
CREATE OR REPLACE VIEW mart.v_origin AS
SELECT
    origin,
    sr_type,
    count(*) AS requests,
    count(response_hours) AS completed,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY response_hours) AS median_hours,
    percentile_cont(0.9) WITHIN GROUP (ORDER BY response_hours) AS p90_hours
FROM mart.v_requests_clean
GROUP BY 1, 2;
