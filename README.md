# Chicago 311 Response Times

[![CI](https://github.com/FernandoLpz0911/chicago-311-response-times/actions/workflows/ci.yml/badge.svg)](https://github.com/FernandoLpz0911/chicago-311-response-times/actions/workflows/ci.yml)
[![E2E](https://github.com/FernandoLpz0911/chicago-311-response-times/actions/workflows/e2e.yml/badge.svg)](https://github.com/FernandoLpz0911/chicago-311-response-times/actions/workflows/e2e.yml)
[![codecov](https://codecov.io/gh/FernandoLpz0911/chicago-311-response-times/branch/main/graph/badge.svg)](https://codecov.io/gh/FernandoLpz0911/chicago-311-response-times)

When Chicagoans call 311 about a pothole, graffiti, or a broken streetlight, how long do they
wait, and does it depend on where they live or how they report it? This project loads every
311 service request since 2023 from the [Chicago Data Portal](https://data.cityofchicago.org/d/v6vf-nfxy)
into PostgreSQL, answers those questions in SQL, and shows the answers in Tableau and Power BI
dashboards. It is also a test-automation project: the pipeline and SQL are covered by pytest,
and a Playwright suite checks the live portal nightly and on every push for changes that would break the load.

## Findings

- Some services leave one in ten people waiting more than a year: half of bicycle requests
  close within 8.3 days, but the slowest 10% take more than 502 days.
- Where you live matters: an abandoned vehicle in Lincoln Park waits a median of 18 days; in the
  Loop, 2.6 days.
- Garbage cart repairs have slowed from a median of 15 days (2023) to 30 days (2026), while rat
  baiting sped up from 6.7 to 4.5 days.
- How you report mostly does not matter: for 7 of the 10 most common request types, phone,
  website, and app are within 15% of each other.

Details, caveats, and numbers in [docs/findings.md](docs/findings.md). Each finding links to the
SQL that produced it in [sql/analysis/](sql/analysis/).

## Dashboards

- Tableau Public: see [dashboards/tableau/](dashboards/tableau/)
- Power BI: see [dashboards/powerbi/](dashboards/powerbi/)

## How it works

```
Socrata API (v6vf-nfxy)
  -> chi311 load      pages through changes since the last run, keyset on (:updated_at, :id)
  -> raw.service_requests      upsert by sr_number; watermark saved in the same transaction
  -> mart.* views              cleaning, monthly / area / channel / backlog aggregates
  -> chi311 export    CSVs for Tableau Public
     Power BI         imports the mart views directly
```

| Path | What it holds |
|---|---|
| `pipeline/` | Python loader: extract, transform, load, export, CLI |
| `sql/schema/` | tables: `raw.service_requests`, `meta.load_state`, `ref.community_areas` |
| `sql/views/` | analysis views in schema `mart`, shared by both dashboards |
| `sql/analysis/` | one query per finding |
| `tests/` | pytest unit and integration tests |
| `e2e/` | Playwright TypeScript tests against the live portal |

### Cleaning rules

- Duplicates (`duplicate = true`) are dropped.
- `311 INFORMATION ONLY CALL` is dropped: these close within seconds and would drag medians toward zero.
- Other record-only requests are dropped for the same reason: nearly all close within minutes of
  being opened, so there is no response to time. These are `Aircraft Noise Complaint` (1.4 million
  rows, forwarded to the airport), `Tree Trim Request (NO LONGER BEING ACCEPTED)`,
  `Finance Parking Code Enforcement Review`, and any request with origin `Mass Entry` (crews
  logging work they have already done).
- Completed requests closed within 6 minutes of being opened ("instant closures", about 4% of them;
  see [docs/findings.md](docs/findings.md)) are dropped. The city does not say why they close so
  fast (likely a report closed because a work order already exists), and they pull medians toward
  zero. Set the cutoff to 0 to keep them (see below).
- Response time is `closed_date - created_date`, for completed requests only.
- Completed requests with no `closed_date`, or one before `created_date`, are listed in `mart.v_data_issues` instead of being dropped silently.
- Areas are compared by community area (77, stable for decades), not by ward: ward boundaries were redrawn in May 2023, so 2023 ward values mix two maps.

## Run it

Requires Docker, Python 3.12, and Node 18 or newer.

```bash
docker compose up -d --wait db
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"

.venv/bin/chi311 migrate      # create tables and views
.venv/bin/chi311 load-areas   # 77 community area names
.venv/bin/chi311 load         # first run: about 7.5 million rows; later runs: only changes
.venv/bin/chi311 export       # CSVs in exports/
```

Set `SOCRATA_APP_TOKEN` for higher API rate limits (optional). Set `DATABASE_URL` to use a
database other than the local Docker one.

`chi311 export --min-minutes 0 --out exports/with-instant` writes the same CSVs with the instant
closures kept; any other number moves the cutoff. Analysis queries can do the same with
`SET chi311.min_minutes = 0` in a `psql` session.

Run the tests:

```bash
.venv/bin/pytest --cov                       # needs the Docker database running
cd e2e && npm install && npx playwright install chromium && npx playwright test
```

## What the tests catch

**pytest** (the code in this repo; coverage is reported to Codecov):

- API paging that skips or repeats rows, and wrong retry behavior on rate limits and server errors.
- Type mistakes when parsing API rows: time zones, booleans, numbers sent as strings, missing fields.
- A re-run that duplicates rows, an update that fails to overwrite, and a crash that advances the watermark past rows that were never saved.
- Wrong numbers in any view. Every view is checked against values worked out by hand from a 13-row fixture that includes a duplicate, an info call, an open request, a canceled request, and two broken timestamps.
- Exports with missing columns or rows.

**Playwright** (the live Chicago Data Portal, nightly and on every push):

- A renamed, removed, or retyped field the loader depends on.
- A change in timestamp format, `$where` filtering, `$limit`, or keyset ordering that would make an incremental load skip or repeat rows.
- Malformed queries no longer failing loudly.
- Mistakes the mocked unit tests cannot see. Example: the live API rejects `$select=:id,:updated_at,*` with HTTP 400 because the star must come first. The contract tests found this; the unit tests mock the API and passed.
- The dataset page, its column list, CSV export, or catalog search breaking.

A nightly E2E failure with no code change means the portal changed. The HTML report and traces
are attached to the workflow run.

## Known limitations

- The portal sometimes re-publishes the whole dataset, which resets `:updated_at` on every row. The next `chi311 load` then refetches everything. That is slow but correct, because the load is idempotent.
- Rows deleted on the portal stay in `raw.service_requests`, because the incremental load cannot see deletions.
- The portal answers queries from several copies of the data, and a newly stamped batch can be missing from some copies for half an hour or more. Each `chi311 load` therefore rereads the last day behind its saved watermark. A row still missing after a day is picked up the next time it changes.
- Timestamps are Chicago local time with no time zone, as published.
- Some request types (for example aircraft noise complaints) close almost instantly by design. Compare response times within a type, not across types.
