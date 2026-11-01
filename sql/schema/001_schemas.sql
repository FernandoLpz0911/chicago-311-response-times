-- raw:  data as published by the city
-- meta: pipeline bookkeeping
-- ref:  reference tables (community area names)
-- mart: analysis views; created and rebuilt by pipeline/migrate.py
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS meta;
CREATE SCHEMA IF NOT EXISTS ref;
