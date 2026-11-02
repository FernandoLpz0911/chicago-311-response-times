-- The requests every metric is built from. Removes:
--   * duplicates: the city flags a repeat report of the same problem with duplicate = true
--   * 311 INFORMATION ONLY CALL: closed within seconds, would pull every median toward zero
--   * other record-only requests, closed on intake with no work to time: Aircraft Noise
--     Complaint (forwarded to the airport), Tree Trim Request (NO LONGER BEING ACCEPTED),
--     Finance Parking Code Enforcement Review, and anything entered with origin Mass Entry
--     (crews logging work already done)
--   * completed requests whose closed_date is missing or earlier than created_date
--     (listed in mart.v_data_issues instead of disappearing silently)
--   * completed requests closed within 6 minutes of being opened ("instant closures":
--     no work to time). A session can change the cutoff with chi311.min_minutes
--     (chi311 export --min-minutes); 0 keeps every completed request
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
  AND sr_type IS DISTINCT FROM 'Aircraft Noise Complaint'
  AND sr_type IS DISTINCT FROM 'Tree Trim Request (NO LONGER BEING ACCEPTED)'
  AND sr_type IS DISTINCT FROM 'Finance Parking Code Enforcement Review'
  AND origin IS DISTINCT FROM 'Mass Entry'
  AND (
      status IS DISTINCT FROM 'Completed'
      OR (closed_date IS NOT NULL AND closed_date >= created_date)
  )
  AND (
      status IS DISTINCT FROM 'Completed'
      OR closed_date - created_date >= make_interval(
          mins => coalesce(nullif(current_setting('chi311.min_minutes', true), '')::int, 6)
      )
  );
