-- One row per 311 request, as published on the Chicago Data Portal (dataset v6vf-nfxy).
-- created_date, closed_date and last_modified_date are Socrata "floating" timestamps:
-- they carry no time zone and are America/Chicago local time.
-- source_row_id and source_updated_at are the Socrata system fields :id and :updated_at.
CREATE TABLE IF NOT EXISTS raw.service_requests (
    sr_number           text PRIMARY KEY,
    sr_type             text,
    sr_short_code       text,
    owner_department    text,
    status              text,
    origin              text,
    created_date        timestamp NOT NULL,
    closed_date         timestamp,
    last_modified_date  timestamp,
    duplicate           boolean,
    legacy_record       boolean,
    parent_sr_number    text,
    ward                integer,
    community_area      integer,
    latitude            double precision,
    longitude           double precision,
    source_row_id       text NOT NULL,
    source_updated_at   timestamptz NOT NULL,
    loaded_at           timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS service_requests_created_date_idx
    ON raw.service_requests (created_date);
CREATE INDEX IF NOT EXISTS service_requests_sr_type_idx
    ON raw.service_requests (sr_type);
CREATE INDEX IF NOT EXISTS service_requests_community_area_idx
    ON raw.service_requests (community_area);
CREATE INDEX IF NOT EXISTS service_requests_status_idx
    ON raw.service_requests (status);
