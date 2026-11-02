-- Completed requests whose timestamps cannot produce a response time.
-- Their count is itself a data-quality finding.
CREATE OR REPLACE VIEW mart.v_data_issues AS
SELECT
    sr_number,
    sr_type,
    status,
    created_date,
    closed_date,
    CASE
        WHEN closed_date IS NULL THEN 'completed_without_closed_date'
        ELSE 'closed_before_created'
    END AS reason
FROM raw.service_requests
WHERE status = 'Completed'
  AND (closed_date IS NULL OR closed_date < created_date);
