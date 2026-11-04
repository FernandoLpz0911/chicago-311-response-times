from datetime import date

import pytest
from psycopg.rows import dict_row

POTHOLE = "Pothole in Street Complaint"
GRAFFITI = "Graffiti Removal Request"


def _query(conn, sql):
    with conn.cursor(row_factory=dict_row) as cur:
        return cur.execute(sql).fetchall()


def _stats(row):
    """(requests, completed, median, p90) with floats wrapped for approximate comparison."""

    def approx(value):
        return None if value is None else pytest.approx(value)

    return (
        row["requests"],
        row["completed"],
        approx(row["median_hours"]),
        approx(row["p90_hours"]),
    )


def test_city_month(loaded):
    rows = _query(loaded, "SELECT * FROM mart.v_city_month ORDER BY month")
    assert [r["month"] for r in rows] == [date(2024, 1, 1), date(2024, 2, 1)]
    # January: completed hours [2, 10, 24, 30, 48]; open graffiti 08 adds a request
    assert _stats(rows[0]) == (6, 5, 24, 40.8)
    # February: pothole 04 (4h), open pothole 05, canceled pothole 13
    assert _stats(rows[1]) == (3, 1, 4, 4)


def test_type_month(loaded):
    rows = {
        (r["sr_type"], r["month"]): _stats(r)
        for r in _query(loaded, "SELECT * FROM mart.v_type_month")
    }
    assert rows == {
        (POTHOLE, date(2024, 1, 1)): (3, 3, 24, 43.2),
        (POTHOLE, date(2024, 2, 1)): (3, 1, 4, 4),
        (GRAFFITI, date(2024, 1, 1)): (3, 2, 16, 27.2),
    }


def test_area_type_compares_areas_within_a_type(loaded):
    rows = {
        (r["community_area"], r["area_name"], r["sr_type"]): _stats(r)
        for r in _query(loaded, "SELECT * FROM mart.v_area_type")
    }
    assert rows == {
        (1, "ROGERS PARK", POTHOLE): (3, 2, 29, 44.2),
        (2, "WEST RIDGE", POTHOLE): (3, 2, 14, 22),
        (1, "ROGERS PARK", GRAFFITI): (3, 2, 16, 27.2),
    }


def test_backlog_ages_open_requests_from_latest_created_date(loaded):
    rows = _query(loaded, "SELECT * FROM mart.v_backlog ORDER BY sr_type")
    # As of 2024-02-25 08:00 (latest created_date): pothole 05 is 4 days 20 hours old,
    # graffiti 08 is 26 days old.
    assert [(r["sr_type"], r["age_bucket"], r["open_requests"]) for r in rows] == [
        (GRAFFITI, "3: 7-30 days", 1),
        (POTHOLE, "2: 1-7 days", 1),
    ]


def test_backlog_bucket_edges(loaded):
    # Move the open pothole so it is exactly 1 day, then 90 days, older than the as-of time.
    def bucket_for(created):
        loaded.execute(
            "UPDATE raw.service_requests SET created_date = %s WHERE sr_number = 'SR24-00000005'",
            (created,),
        )
        return _query(
            loaded, f"SELECT age_bucket FROM mart.v_backlog WHERE sr_type = '{POTHOLE}'"
        )[0]["age_bucket"]

    assert bucket_for("2024-02-24 08:00:01") == "1: <1 day"
    assert bucket_for("2024-02-24 08:00:00") == "2: 1-7 days"
    assert bucket_for("2024-01-26 08:00:00") == "4: 30-90 days"
    assert bucket_for("2023-11-27 08:00:00") == "5: 90+ days"


def test_origin_within_type(loaded):
    rows = {
        (r["origin"], r["sr_type"]): _stats(r)
        for r in _query(loaded, "SELECT * FROM mart.v_origin")
    }
    assert rows == {
        ("Phone Call", POTHOLE): (2, 2, 17, 22.6),
        ("Internet", POTHOLE): (2, 1, 48, 48),
        ("Mobile Device", POTHOLE): (1, 1, 4, 4),
        ("Alderman's Office", POTHOLE): (1, 0, None, None),
        ("Internet", GRAFFITI): (1, 1, 2, 2),
        ("Phone Call", GRAFFITI): (1, 1, 30, 30),
        ("Mobile Device", GRAFFITI): (1, 0, None, None),
    }


def test_area_centroid(loaded):
    rows = _query(loaded, "SELECT * FROM mart.v_area_centroid ORDER BY community_area")
    assert [(r["community_area"], r["area_name"], r["requests"]) for r in rows] == [
        (1, "ROGERS PARK", 6),
        (2, "WEST RIDGE", 3),
    ]
    assert rows[0]["latitude"] == pytest.approx(42.01)
    assert rows[0]["longitude"] == pytest.approx(-87.67)
    assert rows[1]["latitude"] == pytest.approx(41.99)
    assert rows[1]["longitude"] == pytest.approx(-87.69)


def test_type_summary_covers_the_whole_period(loaded):
    rows = {
        r["sr_type"]: _stats(r) for r in _query(loaded, "SELECT * FROM mart.v_type_summary")
    }
    # Potholes across January and February: completed hours [4, 10, 24, 48]
    assert rows == {
        POTHOLE: (6, 4, 17, 40.8),
        GRAFFITI: (3, 2, 16, 27.2),
    }
