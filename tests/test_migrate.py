from pipeline.migrate import SQL_ROOT, apply_migrations

SCHEMA_FILES = [
    "schema/001_schemas.sql",
    "schema/002_raw_service_requests.sql",
    "schema/003_meta_load_state.sql",
    "schema/004_ref_community_areas.sql",
]


def test_sql_root_points_at_repo_sql_dir():
    assert (SQL_ROOT / "schema" / "001_schemas.sql").is_file()


def test_migrations_create_tables(conn):
    rows = conn.execute(
        "SELECT table_schema || '.' || table_name FROM information_schema.tables "
        "WHERE table_schema IN ('raw', 'meta', 'ref') ORDER BY 1"
    ).fetchall()
    assert [r[0] for r in rows] == [
        "meta.load_state",
        "raw.service_requests",
        "ref.community_areas",
    ]


def test_migrations_create_mart_schema(conn):
    row = conn.execute(
        "SELECT 1 FROM information_schema.schemata WHERE schema_name = 'mart'"
    ).fetchone()
    assert row == (1,)


def test_migrations_are_idempotent_and_ordered(conn):
    applied = apply_migrations(conn)
    assert applied[: len(SCHEMA_FILES)] == SCHEMA_FILES


def test_load_state_allows_only_one_row(conn):
    conn.execute("INSERT INTO meta.load_state (id, updated_at, row_id) VALUES (1, 'a', 'b')")
    row = conn.execute(
        "SELECT count(*) FROM pg_constraint WHERE conname LIKE 'load_state_id_check%'"
    ).fetchone()
    assert row[0] == 1
