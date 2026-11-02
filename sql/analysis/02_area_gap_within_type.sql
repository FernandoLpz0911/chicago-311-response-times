-- For the 10 busiest request types: does where you live change how fast the city responds?
-- Compares the fastest and slowest community area for each type. Areas with fewer than 50
-- completed requests of that type are left out so one odd case cannot set the median.
WITH top_types AS (
    SELECT sr_type
    FROM mart.v_requests_clean
    GROUP BY sr_type
    ORDER BY count(*) DESC
    LIMIT 10
),
ranked AS (
    SELECT
        a.sr_type,
        a.area_name,
        a.median_hours,
        row_number() OVER (PARTITION BY a.sr_type ORDER BY a.median_hours ASC) AS fastest_rank,
        row_number() OVER (PARTITION BY a.sr_type ORDER BY a.median_hours DESC) AS slowest_rank
    FROM mart.v_area_type AS a
    JOIN top_types AS t USING (sr_type)
    WHERE a.completed >= 50
)
SELECT
    f.sr_type,
    f.area_name AS fastest_area,
    round(f.median_hours::numeric, 1) AS fastest_median_hours,
    s.area_name AS slowest_area,
    round(s.median_hours::numeric, 1) AS slowest_median_hours,
    round((s.median_hours / NULLIF(f.median_hours, 0))::numeric, 1) AS gap_ratio
FROM ranked AS f
JOIN ranked AS s ON s.sr_type = f.sr_type AND s.slowest_rank = 1
WHERE f.fastest_rank = 1
ORDER BY gap_ratio DESC NULLS LAST;
