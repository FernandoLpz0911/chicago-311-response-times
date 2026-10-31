# Chicago 311 Response Times — Design

Date: 2026-10-31
Status: Approved (brainstorming)

## Purpose

A learning project with two goals: build real skill in data analysis and test automation, and learn how Chicago actually works through the requests its residents make to 311.

### Learning goals

- **Data analysis:** load Chicago's 311 Service Requests open dataset into PostgreSQL, write analysis SQL that goes past basics (CTEs, window functions, percentiles, controlling for mix), and build the same dashboards in both Tableau Public and Power BI to learn how the two tools differ.
- **Test automation:** test the project the way a QA engineer would. pytest covers the pipeline and SQL, with coverage as a feedback loop on what is still untested. A Playwright TypeScript suite runs end-to-end and API contract tests against the public Chicago Data Portal that feeds the pipeline.
- **Engineering practice:** incremental loading, idempotent upserts, CI on every push, and handling a real third-party API that changes without notice.

### Questions about Chicago

The analysis exists to answer questions about the city, not to produce charts for their own sake:

- What do Chicagoans ask the city for, and how does that change with the seasons?
- Which services does the city deliver quickly, and which leave people waiting for weeks?
- Does where you live change how fast the city responds to the same kind of request?
- Is service getting faster or slower since 2023, and does the way you report (phone, app, web) matter?

Along the way the project should build working knowledge of the city's geography (the 77 community areas, the 2023 ward remap) and of which departments own which services.

## Decisions

| Topic | Decision | Reason |
|---|---|---|
| Repo structure | One repo for pipeline, analysis, and tests | Testing code you wrote yourself teaches more than testing a stranger's app; coverage measures code we own |
| Dashboards | Tableau Public first, then Power BI | Learning both tools on the same data shows how they differ; Tableau Public gives a shareable live link. Shared SQL views keep the second dashboard to mostly layout work |
| Data scope | 2023-01-01 to present, incremental | Enough for year-over-year analysis; keeps DB and extracts manageable |
| SQL organization | Plain SQL files, applied by a Python loader | Writing the SQL directly builds the core skill; no framework hiding it. dbt can come later once the SQL is solid |
| E2E language | TypeScript with `@playwright/test` | Playwright's primary runner and the most widely used in practice; HTML report and trace viewer; practice in a second language alongside Python |
| Geography | Community area (77, stable), not ward | Ward map was redrawn in May 2023, so 2023 ward values mix two maps |
| Coverage badge | Codecov (free for public repos) | Learn a standard CI coverage service; line-level reports show what is untested. Requires signup and repo token |

## Architecture and data flow

```
Socrata API (dataset v6vf-nfxy, data.cityofchicago.org)
  -> pipeline/extract.py   page through API; $where :updated_at > watermark
  -> pipeline/load.py      upsert into raw.service_requests (ON CONFLICT sr_number)
  -> sql/views/*.sql       analysis views
  -> pipeline/export.py    views -> exports/*.csv  -> Tableau Public
                           Power BI (Windows) imports from the same Postgres views
```

**Incremental loading.** The watermark is the Socrata system field `:updated_at`, not `created_date`. A request created in March may close in May; only `:updated_at` picks up that closure on a later run. The first run seeds with `created_date >= '2023-01-01'`.

### Repository layout

```
docker-compose.yml          Postgres 16
pipeline/                   Python package: extract, load, migrate, export, CLI
sql/schema/                 raw + meta tables, indexes
sql/views/                  analysis views shared by both dashboards
sql/analysis/               one query file per published finding
tests/                      pytest: unit + integration
tests/fixtures/             small hand-checked 311 sample
e2e/                        Playwright TypeScript project
dashboards/tableau/         public link + screenshots
dashboards/powerbi/         .pbix + screenshots
docs/findings.md            findings about Chicago
.github/workflows/ci.yml    lint + pytest + coverage
.github/workflows/e2e.yml   Playwright, on push + nightly
```

## Data model

### Raw table: `raw.service_requests`

Mirrors API fields with minimal transformation. Expected columns (to be confirmed against the live API in the first implementation task): `sr_number` (primary key), `sr_type`, `sr_short_code`, `owner_department`, `status`, `origin`, `created_date`, `closed_date`, `last_modified_date`, `duplicate`, `legacy_record`, `parent_sr_number`, `ward`, `community_area`, `latitude`, `longitude`, plus the Socrata `:updated_at` value stored as `source_updated_at`.

Socrata timestamps are floating (no time zone). They are stored as `timestamp without time zone` and documented as America/Chicago local time.

### Load state: `meta.load_state`

Holds the current watermark. It advances only after a page's upsert commits.

### Cleaning rules (in `v_requests_clean`)

- Exclude `duplicate = true`.
- Exclude `sr_type = '311 INFORMATION ONLY CALL'` (these close instantly and pull medians toward zero).
- `response_hours = EXTRACT(EPOCH FROM closed_date - created_date) / 3600`, computed only for `status = 'Completed'`.
- Rows with completed status but a null or negative response time are excluded from metrics and surfaced in `v_data_issues` with a reason code, not silently dropped.

### Analysis views

- `v_type_month` — per request type per month: request count, completed count, median and p90 `response_hours` (`percentile_cont`).
- `v_area_type` — median and p90 by community area **within** request type, so area comparisons are not confounded by request mix.
- `v_backlog` — open requests by age bucket (<1 day, 1–7 days, 7–30 days, 30–90 days, 90+ days).
- `v_origin` — response time by intake channel (phone, mobile app, internet, etc.).
- `v_area_centroid` — community area centroid from request coordinates, for the Tableau map.
- `v_data_issues` — rows failing cleaning rules, with reason.

### Candidate findings

Final findings are chosen after exploring the data, guided by the questions about Chicago above. Starting hypotheses:

1. Request types with the widest p90-to-median gap: services where most people are helped quickly but some wait a very long time.
2. Community-area differences in response time within the same request type.
3. Year-over-year trend, or intake-channel effect, for the top 10 request types.

A finding that disproves a hypothesis is as valuable as one that confirms it.

Each published finding gets its own file in `sql/analysis/`.

## Error handling

- HTTP 429 and 5xx: retry with exponential backoff, fail loudly after 5 attempts.
- Each page is upserted in a single transaction; the watermark advances only after commit, so a crashed run resumes without gaps or duplicates.
- Migrations are idempotent (`CREATE ... IF NOT EXISTS`, `CREATE OR REPLACE VIEW`) and applied in filename order.
- An optional Socrata app token is read from an environment variable; the pipeline works without it at lower rate limits.

## Testing

### pytest (Python, code we own — measured by coverage)

- **Unit:** API paging, record parsing and type coercion, watermark logic, retry/backoff behavior. HTTP is mocked.
- **Integration (real Postgres):** Docker locally, service container in CI.
  - Loading the same fixture twice yields identical rows (idempotent upsert).
  - An updated record overwrites the earlier version.
  - Each view's output matches values hand-computed from the fixture.
  - Rows planted with bad data appear in `v_data_issues` with the right reason.
  - Exported CSVs have the expected columns and row counts.
- `pytest-cov` on `pipeline/`; CI fails under 85%.

### Playwright (TypeScript, against data.cityofchicago.org)

- **API contract tests** (Playwright `request` fixture): the SODA endpoint returns the fields the pipeline depends on with expected types; `$where`, `$order`, and `$limit` behave as the loader assumes; a malformed query returns HTTP 400. These catch upstream schema or behavior changes before they break the loader.
- **UI tests** (page object model): dataset page loads with the expected title; the column list contains the fields the pipeline uses; site search finds the dataset; the export menu offers CSV.
- **Flake control:** 2 retries in CI, trace on first retry, HTML report uploaded as a workflow artifact. Queries use small `$limit` values to keep load on the portal light.

### CI

- `ci.yml` — on push and pull request: ruff lint, pytest with a `postgres:16` service, Codecov upload.
- `e2e.yml` — on push and nightly cron: install Chromium, run Playwright, upload HTML report. A nightly failure with no code change means the portal changed.

## Dashboards

Built manually by the project owner. The implementation plan supplies an exact build checklist (sheets, fields, filters).

- **Tableau Public** from `exports/*.csv`. Exports are aggregated views (thousands of rows, not millions), well within Tableau Public limits. Pages:
  1. Overview — volume, median, p90, open backlog.
  2. Request-type explorer — monthly median and p90 by type.
  3. Community-area map — centroid points; upgrade to a filled map if Tableau Public web authoring accepts the city's community-area GeoJSON (verify during the dashboard task).
- **Power BI** on Windows, Import mode from the same Postgres views, same three pages. Commit the `.pbix` and screenshots.

## Write-up

- `docs/findings.md` — for each finding: the claim, the supporting number, a chart screenshot, a link to its `sql/analysis/` file, and a caveat.
- `README.md` — badges (CI, e2e, coverage), a one-paragraph summary, the findings as bullets, the Tableau Public link, run instructions, and a "what the tests catch" section.

## Manual steps for the project owner

- Create a Codecov account and add the repo token as a GitHub secret.
- Create a Tableau Public account and build/publish the dashboard.
- Build the Power BI report on Windows.
- Optional: register a Socrata app token for higher rate limits.

## Out of scope

Forecasting or predictive models, dbt, cloud-hosted Postgres, real-time updates.
