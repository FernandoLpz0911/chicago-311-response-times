-- Monthly volume and response time for each request type.
-- percentile_cont ignores NULLs, so open and canceled requests count toward requests only.
CREATE OR REPLACE VIEW mart.v_type_month AS
SELECT
    sr_type,
    date_trunc('month', created_date)::date AS month,
    count(*) AS requests,
    count(response_hours) AS completed,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY response_hours) AS median_hours,
    percentile_cont(0.9) WITHIN GROUP (ORDER BY response_hours) AS p90_hours
FROM mart.v_requests_clean
GROUP BY 1, 2;
