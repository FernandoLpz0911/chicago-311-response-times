"""Command line: chi311 migrate | load-areas | load | export."""

import argparse
from pathlib import Path

import requests

from pipeline.config import Settings
from pipeline.db import connect
from pipeline.export import export_views
from pipeline.extract import fetch_community_areas
from pipeline.load import load_community_areas, run_load
from pipeline.migrate import apply_migrations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="chi311", description="Chicago 311 response times")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("migrate", help="create tables and rebuild views")
    commands.add_parser("load-areas", help="load the 77 community area names")
    commands.add_parser("load", help="load 311 requests changed since the last run")
    export = commands.add_parser("export", help="write dashboard CSVs")
    export.add_argument("--out", type=Path, default=Path("exports"))
    export.add_argument(
        "--min-minutes",
        type=int,
        default=6,
        help="leave out completed requests closed sooner than this many minutes after opening"
        " (default 6; 0 keeps them)",
    )
    args = parser.parse_args(argv)

    settings = Settings.from_env()
    with connect(settings.database_url) as conn:
        if args.command == "migrate":
            for path in apply_migrations(conn):
                print(f"applied {path}")
        elif args.command == "load-areas":
            with requests.Session() as session:
                rows = fetch_community_areas(session, app_token=settings.app_token)
            print(f"loaded {load_community_areas(conn, rows)} community areas")
        elif args.command == "load":
            with requests.Session() as session:
                total = run_load(conn, session, app_token=settings.app_token)
            print(f"done: {total:,} rows loaded")
        elif args.command == "export":
            for view, count in export_views(conn, args.out, args.min_minutes).items():
                print(f"{view}: {count} rows")
    return 0
