-- Chicago's 77 community areas (dataset igwz-8jzy). Their boundaries have been stable for
-- decades, unlike ward boundaries, which were redrawn in May 2023.
CREATE TABLE IF NOT EXISTS ref.community_areas (
    area_number  integer PRIMARY KEY,
    name         text NOT NULL
);
