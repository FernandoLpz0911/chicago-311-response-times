-- The incremental-load watermark: the last (:updated_at, :id) pair committed to
-- raw.service_requests. Both are kept as the exact text the Socrata API returned so they
-- round-trip into the next $where unchanged. Only one row ever exists (id = 1).
CREATE TABLE IF NOT EXISTS meta.load_state (
    id          integer PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    updated_at  text NOT NULL,
    row_id      text NOT NULL,
    saved_at    timestamptz NOT NULL DEFAULT now()
);
