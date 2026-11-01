-- Open requests by age. Age is measured from the latest created_date in the data (the
-- snapshot time) rather than now(), so results do not drift between loads.
CREATE OR REPLACE VIEW mart.v_backlog AS
WITH as_of AS (
    SELECT max(created_date) AS ts FROM raw.service_requests
),
open_requests AS (
    SELECT c.sr_type, a.ts - c.created_date AS age
    FROM mart.v_requests_clean AS c
    CROSS JOIN as_of AS a
    WHERE c.status = 'Open'
)
SELECT
    sr_type,
    CASE
        WHEN age < interval '1 day' THEN '1: <1 day'
        WHEN age < interval '7 days' THEN '2: 1-7 days'
        WHEN age < interval '30 days' THEN '3: 7-30 days'
        WHEN age < interval '90 days' THEN '4: 30-90 days'
        ELSE '5: 90+ days'
    END AS age_bucket,
    count(*) AS open_requests
FROM open_requests
GROUP BY 1, 2;
