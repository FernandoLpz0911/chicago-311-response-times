"""Page through the Socrata API using keyset pagination on (:updated_at, :id).

Keyset paging (rather than $offset) means a row that changes mid-run moves to the end of
the ordering instead of shifting every later row and causing one to be skipped.

Socrata's `:id` order is its internal order, not lexicographic, so ids must only be compared
by the API (`$where` and `$order`), never in Python or Postgres.

The portal serves queries from several copies of the dataset, and a freshly stamped batch
of rows can be missing from some copies for half an hour or more. Each run therefore starts
a little behind the saved watermark (see `rewind`) and reads that stretch again.
"""

import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import requests

from pipeline.config import AREAS_URL, DATASET_URL, PAGE_SIZE, SEED_DATE
from pipeline.transform import SOURCE_FIELDS

MAX_ATTEMPTS = 5
REQUEST_TIMEOUT = 120  # seconds; a 50,000-row page can be slow


class ExtractError(RuntimeError):
    """The API rejected a request, or kept failing after every retry."""


@dataclass(frozen=True)
class Watermark:
    updated_at: str
    row_id: str | None  # None: start at updated_at itself, inclusive


def rewind(watermark: Watermark | None, window: timedelta) -> Watermark | None:
    """Move the watermark back by window, so the next run rereads rows near the head."""
    if watermark is None:
        return None
    earlier = datetime.fromisoformat(watermark.updated_at) - window
    return Watermark(earlier.isoformat(timespec="milliseconds").replace("+00:00", "Z"), None)


def watermark_from_row(row: dict[str, Any]) -> Watermark:
    return Watermark(updated_at=row[":updated_at"], row_id=row[":id"])


def build_params(watermark: Watermark | None, seed_date: str, limit: int) -> dict[str, str]:
    where = f"created_date >= '{seed_date}'"
    if watermark is not None and watermark.row_id is None:
        where += f" AND :updated_at >= '{watermark.updated_at}'"
    elif watermark is not None:
        where += (
            f" AND (:updated_at > '{watermark.updated_at}'"
            f" OR (:updated_at = '{watermark.updated_at}' AND :id > '{watermark.row_id}'))"
        )
    return {
        "$select": ",".join((*SOURCE_FIELDS, ":id", ":updated_at")),
        "$where": where,
        "$order": ":updated_at,:id",
        "$limit": str(limit),
    }


def fetch_page(
    session: requests.Session,
    url: str,
    params: dict[str, str],
    *,
    app_token: str | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> list[dict[str, Any]]:
    """GET one page. Retries 429, 5xx and network errors with backoff of 1, 2, 4, 8 seconds."""
    headers = {"X-App-Token": app_token} if app_token else {}
    problem = ""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = session.get(url, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
        except (requests.ConnectionError, requests.Timeout) as exc:
            problem = f"{type(exc).__name__}: {exc}"
        else:
            if response.status_code == 200:
                return response.json()
            if response.status_code != 429 and response.status_code < 500:
                raise ExtractError(
                    f"HTTP {response.status_code} from {url}: {response.text[:500]}"
                )
            problem = f"HTTP {response.status_code}"
        if attempt < MAX_ATTEMPTS:
            sleep(2 ** (attempt - 1))
    raise ExtractError(f"gave up after {MAX_ATTEMPTS} attempts on {url}: {problem}")


def iter_pages(
    session: requests.Session,
    watermark: Watermark | None,
    *,
    seed_date: str = SEED_DATE,
    page_size: int = PAGE_SIZE,
    url: str = DATASET_URL,
    app_token: str | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> Iterator[list[dict[str, Any]]]:
    """Yield pages of rows changed after the watermark, oldest change first."""
    while True:
        params = build_params(watermark, seed_date, page_size)
        rows = fetch_page(session, url, params, app_token=app_token, sleep=sleep)
        if not rows:
            return
        yield rows
        if len(rows) < page_size:
            return
        watermark = watermark_from_row(rows[-1])


def fetch_community_areas(
    session: requests.Session,
    *,
    url: str = AREAS_URL,
    app_token: str | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> list[dict[str, Any]]:
    """Fetch the 77 community areas as rows with keys area_numbe and community."""
    params = {"$select": "area_numbe,community", "$limit": "100"}
    return fetch_page(session, url, params, app_token=app_token, sleep=sleep)
