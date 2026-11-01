import json
import os
from pathlib import Path

import psycopg
import pytest

from pipeline.db import connect
from pipeline.migrate import apply_migrations

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql://chi311:chi311@localhost:5432/chi311_test"
)


@pytest.fixture
def database_url():
    return TEST_DATABASE_URL


@pytest.fixture
def conn(database_url):
    """A freshly migrated, empty test database.

    Skips when Postgres is not running locally, but fails in CI, where a skip would hide a
    broken service container.
    """
    try:
        connection = connect(database_url)
    except psycopg.OperationalError:
        if os.environ.get("CI"):
            raise
        pytest.skip("PostgreSQL not reachable; run `docker compose up -d db`")
    with connection.transaction():
        connection.execute("DROP SCHEMA IF EXISTS raw, meta, ref, mart CASCADE")
    apply_migrations(connection)
    yield connection
    connection.close()


FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def raw_rows():
    """13 API-shaped rows; see the table in the implementation plan, Task 4."""
    return json.loads((FIXTURES / "sample_311.json").read_text())


@pytest.fixture
def area_rows():
    return json.loads((FIXTURES / "community_areas.json").read_text())


@pytest.fixture
def loaded(conn, raw_rows, area_rows):
    """The test database with every fixture row and both community areas loaded."""
    from pipeline.load import load_community_areas, load_page

    load_page(conn, raw_rows)
    load_community_areas(conn, area_rows)
    return conn
