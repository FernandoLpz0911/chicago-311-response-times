-- Citywide monthly volume and response time across all request types.
CREATE OR REPLACE VIEW mart.v_city_month AS
SELECT
    date_trunc('month', created_date)::date AS month,
    count(*) AS requests,
    count(response_hours) AS completed,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY response_hours) AS median_hours,
    percentile_cont(0.9) WITHIN GROUP (ORDER BY response_hours) AS p90_hours
FROM mart.v_requests_clean
GROUP BY 1;
