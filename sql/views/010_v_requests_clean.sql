-- The requests every metric is built from. Removes:
--   * duplicates: the city flags a repeat report of the same problem with duplicate = true
--   * 311 INFORMATION ONLY CALL: closed within seconds, would pull every median toward zero
--   * completed requests whose closed_date is missing or earlier than created_date
--     (listed in mart.v_data_issues instead of disappearing silently)
-- response_hours is set only for completed requests.
CREATE OR REPLACE VIEW mart.v_requests_clean AS
SELECT
    sr_number,
    sr_type,
    owner_department,
    status,
    origin,
    created_date,
    closed_date,
    community_area,
    ward,
    latitude,
    longitude,
    CASE
        WHEN status = 'Completed'
            THEN EXTRACT(EPOCH FROM closed_date - created_date)::double precision / 3600
    END AS response_hours
FROM raw.service_requests
WHERE duplicate IS NOT TRUE
  AND sr_type IS DISTINCT FROM '311 INFORMATION ONLY CALL'
  AND (
      status IS DISTINCT FROM 'Completed'
      OR (closed_date IS NOT NULL AND closed_date >= created_date)
  );
