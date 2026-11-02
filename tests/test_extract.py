from datetime import timedelta
from urllib.parse import parse_qs, urlparse

import pytest
import requests
import responses

from pipeline.extract import (
    ExtractError,
    Watermark,
    build_params,
    fetch_community_areas,
    fetch_page,
    iter_pages,
    rewind,
    watermark_from_row,
)

URL = "https://example.test/resource/abcd-1234.json"


def _row(n, updated_at="2024-03-01T06:00:00.000Z"):
    return {":id": f"row-{n:04d}", ":updated_at": updated_at, "sr_number": f"SR{n}"}


def _query(call):
    return {k: v[0] for k, v in parse_qs(urlparse(call.request.url).query).items()}


def test_build_params_first_run_filters_on_seed_date_only():
    assert build_params(None, "2023-01-01", 50) == {
        "$select": (
            "sr_number,sr_type,sr_short_code,owner_department,status,origin,parent_sr_number,"
            "created_date,closed_date,last_modified_date,duplicate,legacy_record,"
            "ward,community_area,latitude,longitude,:id,:updated_at"
        ),
        "$where": "created_date >= '2023-01-01'",
        "$order": ":updated_at,:id",
        "$limit": "50",
    }


def test_build_params_with_watermark_uses_keyset_condition():
    wm = Watermark(updated_at="2024-03-01T06:00:00.000Z", row_id="row-0007")
    assert build_params(wm, "2023-01-01", 50)["$where"] == (
        "created_date >= '2023-01-01' AND (:updated_at > '2024-03-01T06:00:00.000Z'"
        " OR (:updated_at = '2024-03-01T06:00:00.000Z' AND :id > 'row-0007'))"
    )


def test_build_params_without_row_id_reads_from_the_timestamp_inclusive():
    wm = Watermark(updated_at="2024-03-01T06:00:00.000Z", row_id=None)
    assert build_params(wm, "2023-01-01", 50)["$where"] == (
        "created_date >= '2023-01-01' AND :updated_at >= '2024-03-01T06:00:00.000Z'"
    )


def test_rewind_moves_the_watermark_back_and_drops_the_row_id():
    wm = Watermark(updated_at="2024-03-02T06:00:05.120Z", row_id="row-0007")
    assert rewind(wm, timedelta(days=1)) == Watermark("2024-03-01T06:00:05.120Z", None)


def test_rewind_of_no_watermark_is_none():
    assert rewind(None, timedelta(days=1)) is None


def test_watermark_from_row():
    assert watermark_from_row(_row(3)) == Watermark("2024-03-01T06:00:00.000Z", "row-0003")


@responses.activate
def test_fetch_page_returns_rows_and_sends_app_token():
    responses.add(responses.GET, URL, json=[_row(1)], status=200)
    rows = fetch_page(requests.Session(), URL, {"$limit": "1"}, app_token="tok")
    assert rows == [_row(1)]
    assert responses.calls[0].request.headers["X-App-Token"] == "tok"
    assert _query(responses.calls[0]) == {"$limit": "1"}


@responses.activate
def test_fetch_page_omits_app_token_header_when_none():
    responses.add(responses.GET, URL, json=[], status=200)
    fetch_page(requests.Session(), URL, {})
    assert "X-App-Token" not in responses.calls[0].request.headers


@responses.activate
def test_fetch_page_retries_429_and_5xx_with_backoff():
    responses.add(responses.GET, URL, status=429)
    responses.add(responses.GET, URL, status=503)
    responses.add(responses.GET, URL, json=[_row(1)], status=200)
    sleeps = []
    assert fetch_page(requests.Session(), URL, {}, sleep=sleeps.append) == [_row(1)]
    assert sleeps == [1, 2]


@responses.activate
def test_fetch_page_retries_connection_errors():
    responses.add(responses.GET, URL, body=requests.ConnectionError("connection reset"))
    responses.add(responses.GET, URL, json=[], status=200)
    sleeps = []
    assert fetch_page(requests.Session(), URL, {}, sleep=sleeps.append) == []
    assert sleeps == [1]


@responses.activate
def test_fetch_page_gives_up_after_five_attempts():
    for _ in range(5):
        responses.add(responses.GET, URL, status=500)
    sleeps = []
    with pytest.raises(ExtractError, match="gave up after 5 attempts"):
        fetch_page(requests.Session(), URL, {}, sleep=sleeps.append)
    assert sleeps == [1, 2, 4, 8]
    assert len(responses.calls) == 5


@responses.activate
def test_fetch_page_does_not_retry_client_errors():
    responses.add(
        responses.GET, URL, json={"errorCode": "query.soql.no-such-column"}, status=400
    )
    with pytest.raises(ExtractError, match="HTTP 400"):
        fetch_page(requests.Session(), URL, {}, sleep=lambda seconds: None)
    assert len(responses.calls) == 1


@responses.activate
def test_iter_pages_walks_keyset_until_short_page():
    responses.add(responses.GET, URL, json=[_row(1), _row(2)], status=200)
    responses.add(responses.GET, URL, json=[_row(3)], status=200)
    pages = list(
        iter_pages(requests.Session(), None, seed_date="2023-01-01", page_size=2, url=URL)
    )
    assert pages == [[_row(1), _row(2)], [_row(3)]]
    assert len(responses.calls) == 2
    assert _query(responses.calls[0])["$where"] == "created_date >= '2023-01-01'"
    assert ":id > 'row-0002'" in _query(responses.calls[1])["$where"]


@responses.activate
def test_iter_pages_stops_on_empty_page():
    responses.add(responses.GET, URL, json=[_row(1), _row(2)], status=200)
    responses.add(responses.GET, URL, json=[], status=200)
    pages = list(
        iter_pages(requests.Session(), None, seed_date="2023-01-01", page_size=2, url=URL)
    )
    assert pages == [[_row(1), _row(2)]]
    assert len(responses.calls) == 2


@responses.activate
def test_iter_pages_starts_from_given_watermark():
    responses.add(responses.GET, URL, json=[], status=200)
    wm = Watermark("2024-03-01T06:00:05.000Z", "row-0013")
    pages = list(iter_pages(requests.Session(), wm, seed_date="2023-01-01", page_size=2, url=URL))
    assert pages == []
    assert ":id > 'row-0013'" in _query(responses.calls[0])["$where"]


@responses.activate
def test_fetch_community_areas_selects_number_and_name():
    responses.add(responses.GET, URL, json=[{"area_numbe": "1", "community": "ROGERS PARK"}])
    rows = fetch_community_areas(requests.Session(), url=URL)
    assert rows == [{"area_numbe": "1", "community": "ROGERS PARK"}]
    assert _query(responses.calls[0]) == {"$select": "area_numbe,community", "$limit": "100"}
