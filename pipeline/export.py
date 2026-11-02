"""Write the aggregated mart views to CSV files for Tableau Public, which cannot read
Postgres directly. v_requests_clean is not exported: it has millions of rows."""

from pathlib import Path

import psycopg

EXPORT_VIEWS = (
    "v_city_month",
    "v_type_month",
    "v_area_type",
    "v_backlog",
    "v_origin",
    "v_area_centroid",
)


def export_views(conn: psycopg.Connection, out_dir: Path, min_minutes: int = 6) -> dict[str, int]:
    """Write one CSV per view, header included. Returns data-row counts by view.

    Completed requests closed sooner than min_minutes after being opened are left out;
    0 keeps them. The setting lasts only for this export's transaction."""
    out_dir.mkdir(parents=True, exist_ok=True)
    counts = {}
    with conn.transaction():
        conn.execute("SELECT set_config('chi311.min_minutes', %s, true)", [str(min_minutes)])
        for view in EXPORT_VIEWS:
            copy_sql = (
                f"COPY (SELECT * FROM mart.{view} ORDER BY 1, 2) "
                "TO STDOUT WITH (FORMAT csv, HEADER true)"
            )
            with open(out_dir / f"{view}.csv", "wb") as f, conn.cursor() as cur:
                with cur.copy(copy_sql) as copy:
                    for chunk in copy:
                        f.write(chunk)
            counts[view] = conn.execute(f"SELECT count(*) FROM mart.{view}").fetchone()[0]
    return counts
