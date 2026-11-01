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

See [docs/findings.md](docs/findings.md). Each finding links to the SQL that produced it in
[sql/analysis/](sql/analysis/).

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
- Timestamps are Chicago local time with no time zone, as published.
- Some request types (for example aircraft noise complaints) close almost instantly by design. Compare response times within a type, not across types.
