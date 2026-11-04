-- Volume and response time for each request type over the whole period, for the long-waits
-- dashboard. Medians do not combine, so this cannot be rebuilt from v_type_month.
-- percentile_cont ignores NULLs, so open and canceled requests count toward requests only.
CREATE OR REPLACE VIEW mart.v_type_summary AS
SELECT
    sr_type,
    count(*) AS requests,
    count(response_hours) AS completed,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY response_hours) AS median_hours,
    percentile_cont(0.9) WITHIN GROUP (ORDER BY response_hours) AS p90_hours
FROM mart.v_requests_clean
GROUP BY 1;
