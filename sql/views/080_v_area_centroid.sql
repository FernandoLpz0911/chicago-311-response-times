-- One point per community area (the average location of its requests), for dashboard maps.
CREATE OR REPLACE VIEW mart.v_area_centroid AS
SELECT
    c.community_area,
    a.name AS area_name,
    avg(c.latitude) AS latitude,
    avg(c.longitude) AS longitude,
    count(*) AS requests
FROM mart.v_requests_clean AS c
LEFT JOIN ref.community_areas AS a ON a.area_number = c.community_area
WHERE c.community_area IS NOT NULL
  AND c.latitude IS NOT NULL
  AND c.longitude IS NOT NULL
GROUP BY c.community_area, a.name;
