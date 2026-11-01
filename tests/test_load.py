from datetime import datetime

import psycopg
import pytest
import requests
import responses

from pipeline.extract import Watermark
from pipeline.load import (
    get_watermark,
    load_community_areas,
    load_page,
    run_load,
    set_watermark,
)

URL = "https://example.test/resource/abcd-1234.json"


def _count(conn):
    return conn.execute("SELECT count(*) FROM raw.service_requests").fetchone()[0]


def _snapshot(conn):
    return conn.execute(
        "SELECT sr_number, status, created_date, closed_date, duplicate, community_area, "
        "source_updated_at FROM raw.service_requests ORDER BY sr_number"
    ).fetchall()


def test_load_page_inserts_rows_and_saves_watermark(conn, raw_rows):
    watermark = load_page(conn, raw_rows)
    assert _count(conn) == 13
    assert watermark == Watermark("2024-03-01T06:00:05.000Z", "row-0013")
    assert get_watermark(conn) == watermark


def test_get_watermark_is_none_before_first_load(conn):
    assert get_watermark(conn) is None


def test_load_page_is_idempotent(conn, raw_rows):
    load_page(conn, raw_rows)
    first = _snapshot(conn)
    load_page(conn, raw_rows)
    assert _snapshot(conn) == first
    assert _count(conn) == 13


def test_updated_record_overwrites_earlier_version(conn, raw_rows):
    load_page(conn, raw_rows)
    open_pothole = next(r for r in raw_rows if r["sr_number"] == "SR24-00000005")
    closed = open_pothole | {
        ":updated_at": "2024-03-02T06:00:00.000Z",
        "status": "Completed",
        "closed_date": "2024-02-21T12:00:00.000",
    }
    load_page(conn, [closed])
    status, closed_date = conn.execute(
        "SELECT status, closed_date FROM raw.service_requests "
        "WHERE sr_number = 'SR24-00000005'"
    ).fetchone()
    assert status == "Completed"
    assert closed_date == datetime(2024, 2, 21, 12)
    assert _count(conn) == 13
    assert get_watermark(conn) == Watermark("2024-03-02T06:00:00.000Z", "row-0005")


def test_failed_page_rolls_back_rows_and_watermark(conn, raw_rows):
    load_page(conn, raw_rows[:2])
    saved = get_watermark(conn)
    bad = raw_rows[3] | {"created_date": None}
    with pytest.raises(psycopg.errors.NotNullViolation):
        load_page(conn, [raw_rows[2], bad])
    assert _count(conn) == 2
    assert get_watermark(conn) == saved


def test_set_watermark_keeps_a_single_row(conn):
    set_watermark(conn, Watermark("2024-01-01T00:00:00.000Z", "row-a"))
    set_watermark(conn, Watermark("2024-01-02T00:00:00.000Z", "row-b"))
    assert get_watermark(conn) == Watermark("2024-01-02T00:00:00.000Z", "row-b")
    assert conn.execute("SELECT count(*) FROM meta.load_state").fetchone()[0] == 1


@responses.activate
def test_run_load_pages_through_api_then_resumes_from_watermark(conn, raw_rows):
    responses.add(responses.GET, URL, json=raw_rows[:10])
    responses.add(responses.GET, URL, json=raw_rows[10:])
    messages = []
    total = run_load(
        conn, requests.Session(), url=URL, page_size=10,
        sleep=lambda seconds: None, log=messages.append,
    )
    assert total == 13
    assert _count(conn) == 13
    assert len(messages) == 2
    assert "13 rows" in messages[-1]

    responses.reset()
    responses.add(responses.GET, URL, json=[])
    assert run_load(conn, requests.Session(), url=URL, page_size=10, log=messages.append) == 0
    assert "row-0013" in responses.calls[0].request.url


def test_load_community_areas_upserts(conn, area_rows):
    assert load_community_areas(conn, area_rows) == 2
    load_community_areas(conn, area_rows)
    assert conn.execute(
        "SELECT area_number, name FROM ref.community_areas ORDER BY 1"
    ).fetchall() == [(1, "ROGERS PARK"), (2, "WEST RIDGE")]


def test_load_page_names_the_bad_row_and_stores_nothing(conn, raw_rows):
    load_page(conn, raw_rows[:5])
    before = _snapshot(conn)
    watermark = get_watermark(conn)
    bad = raw_rows[5] | {"ward": "N/A"}
    page = [*raw_rows[6:8], bad]
    with pytest.raises(ValueError, match=bad["sr_number"]) as excinfo:
        load_page(conn, page)
    assert bad[":id"] in str(excinfo.value)
    assert _snapshot(conn) == before
    assert get_watermark(conn) == watermark
