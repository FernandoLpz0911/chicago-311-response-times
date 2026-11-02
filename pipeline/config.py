"""Settings read from the environment, with defaults for the local Docker database."""

import os
from dataclasses import dataclass
from datetime import timedelta

DATASET_URL = "https://data.cityofchicago.org/resource/v6vf-nfxy.json"
AREAS_URL = "https://data.cityofchicago.org/resource/igwz-8jzy.json"
SEED_DATE = "2023-01-01"
PAGE_SIZE = 50_000
# How far behind the saved watermark each load starts, to pick up rows the portal had not
# finished publishing on the previous run.
REREAD_WINDOW = timedelta(days=1)

DEFAULT_DATABASE_URL = "postgresql://chi311:chi311@localhost:5432/chi311"


@dataclass(frozen=True)
class Settings:
    database_url: str
    app_token: str | None

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            database_url=os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL),
            app_token=os.environ.get("SOCRATA_APP_TOKEN") or None,
        )
