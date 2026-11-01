"""Write parsed 311 records and the incremental-load watermark to Postgres."""

import time
from collections.abc import Callable
from typing import Any

import psycopg
import requests

from pipeline.config import DATASET_URL, PAGE_SIZE, SEED_DATE
from pipeline.extract import Watermark, iter_pages, watermark_from_row
from pipeline.transform import COLUMNS, parse_record

_UPSERT = (
    f"INSERT INTO raw.service_requests ({', '.join(COLUMNS)}) "
    f"VALUES ({', '.join(f'%({c})s' for c in COLUMNS)}) "
    "ON CONFLICT (sr_number) DO UPDATE SET "
    + ", ".join(f"{c} = EXCLUDED.{c}" for c in COLUMNS if c != "sr_number")
    + ", loaded_at = now()"
)


def upsert_records(conn: psycopg.Connection, records: list[dict[str, Any]]) -> None:
    with conn.cursor() as cur:
        cur.executemany(_UPSERT, records)


def get_watermark(conn: psycopg.Connection) -> Watermark | None:
    row = conn.execute("SELECT updated_at, row_id FROM meta.load_state WHERE id = 1").fetchone()
    return Watermark(*row) if row else None


def set_watermark(conn: psycopg.Connection, watermark: Watermark) -> None:
    conn.execute(
        "INSERT INTO meta.load_state (id, updated_at, row_id) VALUES (1, %s, %s) "
        "ON CONFLICT (id) DO UPDATE SET updated_at = EXCLUDED.updated_at, "
        "row_id = EXCLUDED.row_id, saved_at = now()",
        (watermark.updated_at, watermark.row_id),
    )


def load_page(conn: psycopg.Connection, rows: list[dict[str, Any]]) -> Watermark:
    """Upsert one API page and advance the watermark in a single transaction.

    If anything fails, neither the rows nor the watermark change, so the next run
    refetches this page.
    """
    watermark = watermark_from_row(rows[-1])
    with conn.transaction():
        upsert_records(conn, [parse_record(r) for r in rows])
        set_watermark(conn, watermark)
    return watermark


def run_load(
    conn: psycopg.Connection,
    session: requests.Session,
    *,
    app_token: str | None = None,
    url: str = DATASET_URL,
    seed_date: str = SEED_DATE,
    page_size: int = PAGE_SIZE,
    sleep: Callable[[float], None] = time.sleep,
    log: Callable[[str], None] = print,
) -> int:
    """Load every row changed since the saved watermark. Returns the number of rows loaded."""
    total = 0
    pages = iter_pages(
        session,
        get_watermark(conn),
        seed_date=seed_date,
        page_size=page_size,
        url=url,
        app_token=app_token,
        sleep=sleep,
    )
    for rows in pages:
        watermark = load_page(conn, rows)
        total += len(rows)
        log(f"loaded {total:,} rows (watermark {watermark.updated_at})")
    return total


def load_community_areas(conn: psycopg.Connection, rows: list[dict[str, Any]]) -> int:
    with conn.transaction(), conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO ref.community_areas (area_number, name) VALUES (%s, %s) "
            "ON CONFLICT (area_number) DO UPDATE SET name = EXCLUDED.name",
            [(int(r["area_numbe"]), r["community"]) for r in rows],
        )
    return len(rows)
