"""Apply the SQL files under sql/ in filename order."""

from pathlib import Path

import psycopg

SQL_ROOT = Path(__file__).resolve().parent.parent / "sql"


def apply_migrations(conn: psycopg.Connection, sql_root: Path = SQL_ROOT) -> list[str]:
    """Apply schema files, then rebuild every view. Returns paths relative to sql_root."""
    applied = []
    with conn.transaction():
        for path in sorted((sql_root / "schema").glob("*.sql")):
            conn.execute(path.read_text())
            applied.append(path.relative_to(sql_root).as_posix())
        # Views are rebuilt from scratch so a changed column list never blocks
        # CREATE OR REPLACE VIEW.
        conn.execute("DROP SCHEMA IF EXISTS mart CASCADE")
        conn.execute("CREATE SCHEMA mart")
        for path in sorted((sql_root / "views").glob("*.sql")):
            conn.execute(path.read_text())
            applied.append(path.relative_to(sql_root).as_posix())
    return applied
