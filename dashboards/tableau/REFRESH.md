# Refreshing the dashboards

The Tableau Public workbook is a snapshot of the data, refreshed by hand once a month, in the
first week after a month ends. There is no reminder: the footer on every dashboard names the
newest month, so it shows how old the data is. The decision behind this page is in
[Decide whether the dashboards get refreshed](https://github.com/FernandoLpz0911/chicago-311-response-times/issues/21).

What a refresh changes:

- The workbook on Tableau Public gets the new data. Only the latest snapshot is public; older
  snapshots are not kept or compared. Month-to-month change shows on the Trends dashboard,
  where the newest full month becomes one more point.

What it does not change:

- `docs/findings.md` and the screenshots in `docs/img/` stay pinned to the 2026-11-04 export.
  The findings are rerun only by choice, not every month.
- The `.twbx` in `dashboards/tableau/` is replaced only when the workbook's design changes
  (sheets, calculations, captions), not on a data-only refresh.

## 1. Load and export (Linux machine)

```bash
.venv/bin/chi311 load      # only the changes since the last run
.venv/bin/chi311 export    # CSVs in exports/
zip -j ~/chi311-tableau-data.zip exports/v_*.csv dashboards/geo/community_areas.geojson
```

## 2. Refresh the workbook (Windows machine)

1. Move the zip to Windows and unzip it over `C:\chi311\data\`, replacing the old files. Keep
   the same folder and file names: the workbook stores the paths.
2. Open the workbook in Tableau Public Desktop and run Data > Refresh All Extracts.

## 3. Check

- The footer names the new snapshot month (the newest `month` in the data).
- The snapshot month does not appear on any trend, and the dashed part covers the three full
  months before it. On the Explore dashboard, `End month` reaches the last full month.
- `Top 10 types` holds the same 10 types as before (the list is in
  [BUILD.md](BUILD.md#top-10-set)), in `v_type_month`, `v_origin` and `areas`. The margin at
  the bottom is thin, so this can change. If it does, update `Trend group` and `Panel order`
  for dashboard 3, review the Building Violation flag on dashboards 2 and 4, and treat it as a
  design change.
- Every caption still holds against its chart. Captions carry no numbers, so they only go
  wrong when a pattern changes. Rewrite any that no longer holds, in the workbook and in
  [sketch.md](sketch.md); that is a design change.
- Hover-check one mark per dashboard against its CSV row.

## 4. Publish

File > Save to Tableau Public As..., under the same name, "Chicago 311 response times", so it
replaces the published workbook. Check that "Allow others to download" is still on.

## 5. Back in the repo

- **Data-only refresh:** commit nothing.
- **Design changed:** save a local `chicago-311-response-times.twbx`, and through a PR into
  `dev` replace the one in `dashboards/tableau/` and update [sketch.md](sketch.md) and
  [BUILD.md](BUILD.md) to match. Leave `docs/findings.md` and its screenshots as they are
  unless the findings are being rerun on purpose.
