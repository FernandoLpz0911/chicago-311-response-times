from datetime import UTC, datetime

from pipeline.transform import COLUMNS, parse_record

# A real row from the API (2026-11-01), trimmed of fields the loader ignores.
API_ROW = {
    ":id": "row-x2ya.a9ji.m34b",
    ":updated_at": "2026-11-01T15:20:09.420Z",
    "sr_number": "SR26-02205113",
    "sr_type": "Aircraft Noise Complaint",
    "sr_short_code": "AVN",
    "owner_department": "Aviation",
    "status": "Completed",
    "origin": "Internet",
    "created_date": "2026-11-01T07:57:20.000",
    "last_modified_date": "2026-11-01T08:31:59.000",
    "closed_date": "2026-11-01T07:57:21.000",
    "street_address": "10510 W ZEMKE RD",
    "duplicate": False,
    "legacy_record": False,
    "community_area": "76",
    "ward": "41",
    "latitude": "41.994900000941",
    "longitude": "-87.887749500002",
}


def test_columns_match_raw_table_order():
    assert COLUMNS == (
        "sr_number", "sr_type", "sr_short_code", "owner_department", "status", "origin",
        "created_date", "closed_date", "last_modified_date", "duplicate", "legacy_record",
        "parent_sr_number", "ward", "community_area", "latitude", "longitude",
        "source_row_id", "source_updated_at",
    )


def test_parse_record_types_every_column():
    record = parse_record(API_ROW)
    assert set(record) == set(COLUMNS)
    assert record["sr_number"] == "SR26-02205113"
    assert record["sr_type"] == "Aircraft Noise Complaint"
    assert record["created_date"] == datetime(2026, 11, 1, 7, 57, 20)
    assert record["created_date"].tzinfo is None
    assert record["closed_date"] == datetime(2026, 11, 1, 7, 57, 21)
    assert record["last_modified_date"] == datetime(2026, 11, 1, 8, 31, 59)
    assert record["duplicate"] is False
    assert record["legacy_record"] is False
    assert record["community_area"] == 76
    assert record["ward"] == 41
    assert record["latitude"] == 41.994900000941
    assert record["longitude"] == -87.887749500002
    assert record["parent_sr_number"] is None
    assert record["source_row_id"] == "row-x2ya.a9ji.m34b"
    assert record["source_updated_at"] == datetime(2026, 11, 1, 15, 20, 9, 420000, tzinfo=UTC)


def test_parse_record_open_request_without_location():
    missing = {"closed_date", "latitude", "longitude", "community_area", "ward", "duplicate"}
    row = {k: v for k, v in API_ROW.items() if k not in missing} | {"status": "Open"}
    record = parse_record(row)
    assert record["status"] == "Open"
    assert record["closed_date"] is None
    assert record["latitude"] is None
    assert record["longitude"] is None
    assert record["community_area"] is None
    assert record["ward"] is None
    assert record["duplicate"] is None


def test_parse_record_accepts_string_booleans_and_float_strings():
    record = parse_record(API_ROW | {"duplicate": "true", "legacy_record": "false", "ward": "41.0"})
    assert record["duplicate"] is True
    assert record["legacy_record"] is False
    assert record["ward"] == 41


def test_parse_record_treats_empty_strings_as_missing():
    record = parse_record(API_ROW | {"origin": "", "community_area": "", "closed_date": ""})
    assert record["origin"] is None
    assert record["community_area"] is None
    assert record["closed_date"] is None
