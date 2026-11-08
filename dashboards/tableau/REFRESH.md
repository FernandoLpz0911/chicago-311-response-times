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

## 1. Load and export

```bash
docker compose up -d --wait db
.venv/bin/chi311 load      # only the changes since the last run
.venv/bin/chi311 export    # CSVs in exports/
```

## 2. Refresh the workbook (web editor)

Uploaded files are copies: Tableau Public does not see the new CSVs until they are uploaded
again.

1. On the workbook's page on Tableau Public, click Edit to open it in the web editor.
2. For each data source, go to its data source page and replace its file with the new export
   of the same name (the data source's menu > Replace, or the file's menu > Edit connection or
   Replace, whichever the editor offers). The boundary file `community_areas.geojson` does not
   change and needs no upload.
3. If the editor offers no way to swap a file in place, note it here on the first refresh and
   find another route before the next one. Removing a file and adding it again can break every
   sheet built on it, so do not do that on a finished workbook.

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

File > Save, under the same name, "Chicago 311 response times", so it replaces the published
workbook. Check that "Allow others to download" is still on.

## 5. Back in the repo

- **Data-only refresh:** commit nothing.
- **Design changed:** download the `.twbx` from the workbook's page on Tableau Public, rename it
  `chicago-311-response-times.twbx`, and through a PR into
  `dev` replace the one in `dashboards/tableau/` and update [sketch.md](sketch.md) and
  [BUILD.md](BUILD.md) to match. Leave `docs/findings.md` and its screenshots as they are
  unless the findings are being rerun on purpose.
