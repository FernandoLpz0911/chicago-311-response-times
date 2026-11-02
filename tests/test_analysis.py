from decimal import Decimal
from pathlib import Path

from psycopg.rows import dict_row

ANALYSIS = Path(__file__).resolve().parent.parent / "sql" / "analysis"
POTHOLE = "Pothole in Street Complaint"
GRAFFITI = "Graffiti Removal Request"


def _run(conn, name):
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute((ANALYSIS / name).read_text())
        return [col.name for col in cur.description], cur.fetchall()


def test_long_tail_types_needs_real_volume(loaded):
    columns, rows = _run(loaded, "01_long_tail_types.sql")
    assert columns == ["sr_type", "completed", "median_hours", "p90_hours", "p90_to_median"]
    assert rows == []  # fixture types have far fewer than 1,000 completed requests


def test_area_gap_needs_real_volume(loaded):
    columns, rows = _run(loaded, "02_area_gap_within_type.sql")
    assert columns == [
        "sr_type", "fastest_area", "fastest_median_hours",
        "slowest_area", "slowest_median_hours", "gap_ratio",
    ]
    assert rows == []  # fixture areas have fewer than 50 completed requests per type


def test_area_gap_ranks_fastest_and_slowest(loaded):
    # Lower the volume threshold to exercise the ranking on fixture data.
    sql = (ANALYSIS / "02_area_gap_within_type.sql").read_text()
    sql = sql.replace("a.completed >= 50", "a.completed >= 1")
    with loaded.cursor(row_factory=dict_row) as cur:
        rows = cur.execute(sql).fetchall()
    assert [
        (r["sr_type"], r["fastest_area"], r["slowest_area"], r["gap_ratio"]) for r in rows
    ] == [
        (POTHOLE, "WEST RIDGE", "ROGERS PARK", Decimal("2.1")),
        (GRAFFITI, "ROGERS PARK", "ROGERS PARK", Decimal("1.0")),
    ]


def test_yoy_top_types(loaded):
    columns, rows = _run(loaded, "03_yoy_top_types.sql")
    assert columns == [
        "sr_type", "requests", "median_2023", "median_2024", "median_2025", "median_2026",
    ]
    assert [(r["sr_type"], r["requests"], r["median_2024"]) for r in rows] == [
        (POTHOLE, 6, Decimal("17.0")),
        (GRAFFITI, 3, Decimal("16.0")),
    ]
    assert all(r["median_2023"] is None and r["median_2026"] is None for r in rows)


def test_origin_effect(loaded):
    columns, rows = _run(loaded, "04_origin_effect.sql")
    assert columns == ["sr_type", "requests", "median_phone", "median_internet", "median_mobile"]
    assert [tuple(r.values()) for r in rows] == [
        (POTHOLE, 6, Decimal("17.0"), Decimal("48.0"), Decimal("4.0")),
        (GRAFFITI, 3, Decimal("30.0"), Decimal("2.0"), None),
    ]
