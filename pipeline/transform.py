"""Turn one Socrata API row into a dict keyed by raw.service_requests column names."""

from datetime import datetime
from typing import Any

COLUMNS = (
    "sr_number", "sr_type", "sr_short_code", "owner_department", "status", "origin",
    "created_date", "closed_date", "last_modified_date", "duplicate", "legacy_record",
    "parent_sr_number", "ward", "community_area", "latitude", "longitude",
    "source_row_id", "source_updated_at",
)

_TEXT = (
    "sr_number", "sr_type", "sr_short_code", "owner_department", "status", "origin",
    "parent_sr_number",
)
_TIMESTAMPS = ("created_date", "closed_date", "last_modified_date")
_BOOLS = ("duplicate", "legacy_record")
_INTS = ("ward", "community_area")
_FLOATS = ("latitude", "longitude")


def _present(value: Any) -> bool:
    return value is not None and value != ""


def _bool(value: Any) -> bool | None:
    if isinstance(value, bool) or value is None:
        return value
    return str(value).lower() == "true"


def parse_record(row: dict[str, Any]) -> dict[str, Any]:
    """Type one API row. Missing or empty fields become None."""
    record: dict[str, Any] = {}
    for name in _TEXT:
        record[name] = row[name] if _present(row.get(name)) else None
    for name in _TIMESTAMPS:
        value = row.get(name)
        # Floating timestamps like "2026-11-01T07:57:20.000" parse to naive datetimes.
        record[name] = datetime.fromisoformat(value) if _present(value) else None
    for name in _BOOLS:
        record[name] = _bool(row.get(name))
    for name in _INTS:
        value = row.get(name)
        record[name] = int(float(value)) if _present(value) else None
    for name in _FLOATS:
        value = row.get(name)
        record[name] = float(value) if _present(value) else None
    record["source_row_id"] = row[":id"]
    record["source_updated_at"] = datetime.fromisoformat(row[":updated_at"])
    return record
