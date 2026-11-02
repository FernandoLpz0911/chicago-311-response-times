-- Does the way you report matter? Median response hours by intake channel, compared within
-- each of the 10 busiest request types so the mix of types does not decide the answer.
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
        FILTER (WHERE c.origin = 'Phone Call'))::numeric, 1) AS median_phone,
    round((percentile_cont(0.5) WITHIN GROUP (ORDER BY c.response_hours)
        FILTER (WHERE c.origin = 'Internet'))::numeric, 1) AS median_internet,
    round((percentile_cont(0.5) WITHIN GROUP (ORDER BY c.response_hours)
        FILTER (WHERE c.origin = 'Mobile Device'))::numeric, 1) AS median_mobile
FROM mart.v_requests_clean AS c
JOIN top_types AS t USING (sr_type)
GROUP BY c.sr_type
ORDER BY requests DESC;
