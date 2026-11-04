# Building the Tableau workbook

Step-by-step notes for building the workbook in Tableau Public Desktop (Tableau Desktop Public
Edition) on Windows. [sketch.md](sketch.md) says *what* each dashboard shows; this page says *how*
to build it. Where the two disagree, the sketch wins. Menu names are from recent Tableau
versions and may differ slightly in yours.

## 1. Get the data onto the Windows machine

The CSVs in `exports/` were exported on 2026-11-04 under the 6-minute rule. Build the workbook
from them; later monthly refreshes follow [REFRESH.md](REFRESH.md). `exports/` is git-ignored, so
the files have to be copied over.

1. On the Linux machine, bundle the seven exports and the boundary file:

   ```bash
   zip -j ~/chi311-tableau-data.zip exports/v_*.csv dashboards/geo/community_areas.geojson
   ```

   Leave out `exports/no-instant/`. It is an old trial export from before the 6-minute rule
   became the default, and it has no `v_type_summary.csv`.
2. Move the zip to Windows (USB stick, cloud drive, or `scp`) and unzip it into one folder,
   for example `C:\chi311\data\`. Keep the folder: the workbook stores the paths.
3. Check the files arrived whole. Data rows per file in the 2026-11-04 export (not counting the
   header):

   | File | Rows |
   |---|---|
   | `v_area_centroid.csv` | 77 |
   | `v_area_type.csv` | 7,326 |
   | `v_backlog.csv` | 387 |
   | `v_city_month.csv` | 47 |
   | `v_origin.csv` | 1,069 |
   | `v_type_month.csv` | 4,436 |
   | `v_type_summary.csv` | 103 |
   | `community_areas.geojson` | 77 features |

   In Tableau, the data source page shows the row count under the grid.

## 2. Data sources

Make one data source per file (Connect > To a File > Text file, or Spatial file for the
GeoJSON). Rename each data source after its file. Separate sources keep every sheet at the grain
of one export, which is what the "never combine medians" rule needs.

The one exception is the map data source for dashboards 2 and 5: connect to
`community_areas.geojson`, then drag `v_area_type.csv` onto the canvas as a related table, with
the relationship `community_area = community_area`. Call it `areas`.

After connecting, check the field types on the data source page:

- `month`: Date (not Date & Time, not String).
- `community_area`: Number (whole) in both the CSV and the GeoJSON.
- `median_hours`, `p90_hours`: Number (decimal). `requests`, `completed`, `open_requests`:
  Number (whole).
- `origin` in `v_origin` has one empty value (415 requests). Leave it; the `Channel` field
  puts it under Other.

### Calculated fields

Create the sketch's calculated fields in each data source that needs them (Analysis > Create
Calculated Field). Copy them across with right-click > Copy, then Paste in the other source.

| Field | Formula | Data sources |
|---|---|---|
| `Median days` | `[median_hours] / 24` | all with `median_hours` |
| `P90 days` | `[p90_hours] / 24` | `v_type_summary`, `v_type_month`, `v_city_month` |
| `Tail ratio` | `[p90_hours] / [median_hours]` | `v_type_summary` |
| `Tail gap` | `[p90_hours] - [median_hours]` | `v_type_summary` |
| `Channel` | see sketch | `v_origin` |
| `Show month` | `[month] < {MAX([month])}` | `v_type_month`, `v_city_month` |
| `Provisional` | `DATEDIFF('month', [month], {MAX([month])}) <= 3` | `v_type_month`, `v_city_month` |

`Channel` maps only `Phone Call` to Phone, as finding 4's SQL does. The 129 requests with
origin `Phone` go to Other; that matches the finding, so leave it.

Format `Median days` and `P90 days` as Number (Custom), 1 decimal place, suffix " days"
(right-click the field > Default Properties > Number Format). Every chart then shows days the
same way.

### Top 10 set

In `v_type_month`, `v_origin` and `areas`, create the Top 10 set on `sr_type`
(right-click `sr_type` > Create > Set > Top tab > By field: Top 10 by `requests`, Sum). Call
it `Top 10 types`. All three hold the same 10 types in the 2026-11-04 export:

> Graffiti Removal Request, Abandoned Vehicle Complaint, Garbage Cart Maintenance, Rodent
> Baiting/Rat Complaint, Tree Debris Clean-Up Request, Street Light Out Complaint, Pothole in
> Street Complaint, Tree Emergency, Blue Recycling Cart, Building Violation

Tree Removal Inspection is 11th. If it shows up in any set, the set is counting something other
than `SUM(requests)`.

### Aggregation

Every sheet that shows `median_hours`, `p90_hours` or a field built from them must have the
export's grouping fields (`sr_type`, `month`, `community_area`, `origin`) on the view, so each
mark is one export row. Then use `MIN()` (or `ATTR()`) on the median, never `SUM` or `AVG`.
A quick check: hover over a mark. The tooltip value should equal the CSV value for that row.

## 3. Shared pieces

**Colours.** Make a custom palette once, or pick these each time:
grey `#BAB0AC` for context, blue `#4E79A7` for the accent and "slowed down", orange `#F28E2B`
for "sped up". These are Tableau 10 colours and are safe for colour-blind viewers.

**Footer.** A small worksheet rather than a text object, so its date follows the data after a
refresh:

1. New sheet `Footer`, data source `v_city_month`. Create the calculated field
   `Newest month = {MAX([month])}`.
2. Drag `Newest month` to Text on the Marks card. Right-click it > Exact Date, and set it to
   Discrete. Right-click > Format > Dates: Custom, `mmmm yyyy`.
3. Click Text on the Marks card > `...` and replace the text with the footer below, inserting
   the field with Insert > `Newest month`:

   > Chicago 311 service requests created from January 2023 to <Newest month>; the newest
   > month is partial. Requests closed within 6 minutes are left out. Waits are medians of
   > completed requests; open requests are not counted. Source and code:
   > https://github.com/FernandoLpz0911/chicago-311-response-times

4. Left-align it, small font. Turn off the tooltip (Worksheet > Tooltip, untick Show tooltips)
   and the sheet title.
5. On every dashboard, drag `Footer` along the bottom, Fit: Entire View, about 60 px high, with
   its title hidden. Text in a worksheet is not a link; to make the repo URL clickable, add
   Dashboard > Actions > Add Action > Go to URL, source sheet `Footer`, run on Select.

Check: the footer reads "... to November 2026; the newest month is partial." with the 2026-11-04
export.

**Dashboard size.** Fixed, 1200 x 800 (Dashboard > Size). Tableau Public shows fixed sizes
reliably; automatic sizes reflow oddly when embedded.

**Titles and captions.** Use the titles and captions from the sketch word for word. Captions
carry no numbers, so they stay true after a refresh unless the pattern itself changes; the
numbers are in the charts and tooltips.

## 4. Dashboard 1: Long waits

Data source: `v_type_summary`.

**Filters** (all on the Filters shelf, none shown to the viewer). Order matters, because
Tableau applies context filters first, then Top N, then measure filters:

1. Create `Enough requests = [completed] >= 1000`, filter it to True, then right-click the
   filter > Add to Context. It must be in context, or the Top 15 is taken over all types.
2. `sr_type`: Top tab > By field: Top 15 by `Tail gap`, Sum.
3. `Tail ratio`: measure filter, at least 6.

The view should have 6 rows: Bicycle Request/Complaint, Street Light On During Day Complaint,
Water Lead Test Kit Request, No Building Permit and Construction Violation, Alley Pothole
Complaint, Sewer Cave-In Inspection Request. These are the six rows of the finding 1 table.

**Dumbbell:**

1. Rows: `sr_type`. Sort it by field `Tail ratio`, Minimum, descending.
2. Columns: `Measure Values`. On the Measure Values card keep only `MIN(Median days)` and
   `MIN(P90 days)`.
3. Drag `Measure Values` to Columns a second time. Right-click the second one > Dual Axis, then
   right-click the axis > Synchronize Axis.
4. First marks card: Circle. Shape: `Measure Names` (filled circle for median, open circle for
   90th percentile).
5. Second marks card: Line. Put `Measure Names` on Path, so each row draws one line between
   its two dots.
6. Colour (both cards): create `Is bicycle = [sr_type] = 'Bicycle Request/Complaint'`, put it on
   Colour, True = blue, False = grey.
7. Edit the x axis: Logarithmic, title "Days (log scale)". Hide the second axis header.
8. Ratio label: on the line card, put `MIN(Tail ratio)` on Label, format as Number (Custom), 0
   decimals, suffix "x", label at the line end only (Label > Line ends > End only).

## 5. Dashboard 2: Where you live

Data source: `areas`.

**Parameter.** Create `Selected type` (String, List). Add from field `sr_type`, then remove all
but the Top 10 types. Current value: Abandoned Vehicle Complaint. Show the parameter control
(single-value dropdown); this is the viewer's type filter.

**Calculated fields:**

- `Enough area requests = [completed] >= 50`
- `Map median days = IF [completed] >= 50 THEN [median_hours] / 24 END`
- `Map note = IF [completed] < 50 THEN 'Too few requests' END`
- `Fastest median = {FIXED [sr_type]: MIN(IF [completed] >= 50 THEN [median_hours] END)}`
- `Slowest median = {FIXED [sr_type]: MAX(IF [completed] >= 50 THEN [median_hours] END)}`
- `Is extreme = [completed] >= 50 AND ([median_hours] = [Fastest median] OR [median_hours] = [Slowest median])`
- `Slow to fast = [Slowest median] / [Fastest median]`
- `Type note = IF [sr_type] = 'Building Violation' THEN 'Covers many kinds of problem, so the gap may reflect what gets reported in each area as much as how fast it is handled.' END`

`Fastest median` and `Slowest median` pick one area's median each; they do not combine medians.

**Map sheet:**

1. Double-click `Geometry` (from the GeoJSON). Tableau draws all 77 areas. Make this layer
   plain grey; it is the background.
2. Drag `Geometry` onto the map again and drop it on "Add a Marks Layer". Everything below goes
   on this top layer only.
3. Create `Is selected type = [sr_type] = [Selected type]` and filter it to True.
4. Colour: `MIN(Map median days)`, sequential (light = fast, dark = slow). Areas under 50
   completed requests, or with no requests of that type, have no value and show the grey
   background.
5. Tooltip: `area_name`, `MIN(Map median days)`, `MIN(completed)`, `ATTR(Map note)`.

Check: with Abandoned Vehicle Complaint, the Loop is lightest (2.7 days) and Lincoln Park
darkest (18.0 days).

**Gap strip sheet:**

1. Filters: `Top 10 types` (In), `Enough area requests` = True.
2. Rows: `sr_type`, sorted by field `Slow to fast`, Minimum, descending.
3. Columns: `MIN(Median days)`. Detail: `community_area`. Mark: Circle.
4. Colour and size: `Is extreme`. True = blue and larger, False = grey and small.
5. Label: `area_name`, shown only for extremes (create
   `Extreme label = IF [Is extreme] THEN [area_name] END` and put that on Label instead).
6. Tooltip: add `ATTR(Type note)`.

**Dashboard:** map on the left, strip on the right. Add a parameter action
(Dashboard > Actions > Add Action > Change Parameter): source the strip, run on Select, target
`Selected type`, field `sr_type`. Clicking a row then sets the map's type and the dropdown.

## 6. Dashboard 3: Trends

Data source: `v_type_month`.

**Calculated fields:**

- `Trend group = CASE [sr_type] WHEN 'Garbage Cart Maintenance' THEN 'Slowed down' WHEN 'Blue Recycling Cart' THEN 'Slowed down' WHEN 'Pothole in Street Complaint' THEN 'Slowed down' WHEN 'Rodent Baiting/Rat Complaint' THEN 'Sped up' WHEN 'Building Violation' THEN 'Sped up' ELSE 'Other' END`
- `Panel order = CASE [sr_type] WHEN 'Garbage Cart Maintenance' THEN 1 WHEN 'Blue Recycling Cart' THEN 2 WHEN 'Pothole in Street Complaint' THEN 3 WHEN 'Rodent Baiting/Rat Complaint' THEN 4 WHEN 'Building Violation' THEN 5 WHEN 'Tree Debris Clean-Up Request' THEN 6 WHEN 'Abandoned Vehicle Complaint' THEN 7 WHEN 'Tree Emergency' THEN 8 WHEN 'Street Light Out Complaint' THEN 9 WHEN 'Graffiti Removal Request' THEN 10 END`
- `Settled days = IF NOT [Provisional] THEN [median_hours] / 24 END`
- `Provisional days = IF DATEDIFF('month', [month], {MAX([month])}) <= 4 THEN [median_hours] / 24 END`
  (one month more than `Provisional`, so the dashed line joins the solid one)
- `First provisional month = DATEADD('month', -3, {MAX([month])})`
- `Last full month = DATEADD('month', -1, {MAX([month])})`

**Small multiples.** Each panel needs its own y axis, and Tableau can only make axes
independent per row or per column of a grid, not per cell. Two ways:

- **One sheet, ten rows (simpler).** Rows: `sr_type` (sorted by `Panel order`) and the measures
  below; Columns: `month` as continuous Month. Edit the y axis: Independent axis ranges for each
  row. The panels stack vertically instead of 2 by 5.
- **Ten sheets in a 2 by 5 grid (matches the sketch).** Build one panel, then duplicate it nine
  times and change only its `sr_type` filter. Arrange them in the dashboard with horizontal
  containers.

For each panel:

1. Filters: `Top 10 types` (In), `Show month` = True.
2. Columns: `month` (continuous Month). Rows: `MIN(Settled days)` and `MIN(Provisional days)`,
   dual axis, synchronized, second axis hidden.
3. Both cards: Line, colour by `Trend group` (Slowed down blue, Sped up orange, Other grey).
4. Provisional card: Path > Line Pattern > dashed (or, in older versions, a lighter colour
   with lower opacity).
5. Reference band on the month axis (Analytics pane > Reference Band, per table): from
   `First provisional month` (Minimum) to `Last full month` (Maximum), light grey fill, label
   "Still settling: many requests open".

Check: the dashed part covers the three full months before the snapshot month, and the
snapshot month (the newest `month`) is not drawn. With the 2026-11-04 export that is August to
October 2026 dashed and November 2026 absent.

## 7. Dashboard 4: How you report

Data source: `v_origin`.

1. Filters: `Top 10 types` (In), `Channel` in Phone, Website, App.
2. Create `Channel gap = {FIXED [sr_type]: MAX(IF [Channel] <> 'Other' THEN [median_hours] END)} / {FIXED [sr_type]: MIN(IF [Channel] <> 'Other' THEN [median_hours] END)}`.
   `FIXED` ignores the `Channel` filter, which is why the condition is inside it.
3. Rows: `sr_type`, sorted by field `Channel gap`, Minimum, descending. Building Violation
   should be on top.
4. Columns: `MIN(Median days)`, dual axis with a second `MIN(Median days)`.
5. First card: Circle, colour by `Channel` (Phone, Website, App: three distinct colours, e.g.
   blue, orange, teal `#76B7B2`), `origin` on Detail.
6. Second card: Line, grey, thin, `Channel` on Path. It draws from the fastest to the slowest
   channel through the middle one, which reads as one line.
7. Label the Building Violation dots: create
   `BV label = IF [sr_type] = 'Building Violation' THEN [median_hours] / 24 END`, put it on
   Label on the circle card.

Check: Building Violation shows Phone 34.8, Website 16.1, App 16.3 days.

## 8. Dashboard 5: Explore

This one has the most moving parts; build it last.

**Parameters:**

- `Explore type` (String, List): add from field `v_type_month` `sr_type`, then add
  "All types" at the top. Current value: All types. Show as a single-value dropdown.
- `Start month` and `End month` (Date, Range, step 1 month). Set the range from field `month`
  in `v_type_month`, refreshed when the workbook opens, so a refresh extends it. Current
  values: `Start month` 2023-01-01; `End month` "Value when workbook opens" = `Last full month`
  (create it in `v_type_month` if it is not there yet). If your version lacks these options,
  type 2023-01-01 to the last full month (2026-10-01 for the 2026-11-04 export) and move the end
  on each refresh. Show both controls (slider). A filter applies to one data source, but a parameter applies
  to all of them, which is why the type and month range are parameters rather than filters.

**In every data source used here, add:**

- `Type match = [Explore type] = 'All types' OR [sr_type] = [Explore type]` (sources with
  `sr_type`), filtered to True.
- `In range = [month] >= [Start month] AND [month] <= [End month] AND [Show month]` (sources
  with `month`), filtered to True.
- `All types picked = [Explore type] = 'All types'` (any one source), for dynamic zone
  visibility.

**Sheets:**

- **Tiles.** Requests and completed: `SUM(requests)` and `SUM(completed)` over the month range
  (counts can be added). Median days: the latest month in the range only, with
  `Latest in range = [month] = {MAX(IF [month] <= [End month] AND [Show month] THEN [month] END)}`
  as a filter, and the month and "(still settling)" when `Provisional` in the tile label. Open
  requests: `SUM(open_requests)` from `v_backlog` with `Type match`. Make one set of tiles from
  `v_city_month` and one from `v_type_month`.
- **Trend.** `Median days` by month, with a thin `P90 days` line, provisional months dashed as on
  dashboard 3. Again one from `v_city_month` and one from `v_type_month`.
- **Map.** As on dashboard 2, but filtered by `[sr_type] = [Explore type]`. Use `area_name` from
  the GeoJSON (or `v_area_centroid`) in the tooltip.
- **By channel.** Bar of `MIN(Median days)` by `Channel` from `v_origin`, filtered to Phone,
  Website and App. Each of those is exactly one origin (Phone Call, Internet, Mobile Device),
  so each bar is one export row. Leave Other out: it spans many origins, and one bar for it
  would combine their medians.
- **Backlog.** Bar of `SUM(open_requests)` by `age_bucket` from `v_backlog`, filtered by
  `Type match`. With All types it adds up all types' open requests, which is fine for counts.

**Switching between All types and one type.** Put the city versions (tiles, trend) and the
type versions in separate containers. Select a container > Layout pane > Control visibility
using value: `All types picked` (city container) or a matching `One type picked` field set to
`NOT [All types picked]` (type container, map, by channel). Map and by channel are hidden with
All types, because the exports have no all-types row per area or per channel.

**Area filter.** Clicking an area on the map highlights it (Dashboard > Actions > Highlight,
source the map). Add a small note under the map: "Area selection applies to the map only: the
other exports have no area column."

Caption: from the sketch.

## 9. Story

New Story (Story > New Story), size 1200 x 900 so the 800-high dashboards fit under the
caption bar. Four story points, one per finding, in the order of `docs/findings.md`:

1. Dashboard 1, caption "1. Long waits".
2. Dashboard 2, caption "2. Where you live".
3. Dashboard 3, caption "3. Trends".
4. Dashboard 4, caption "4. How you report".

Optionally a fifth point, Dashboard 5, "Explore it yourself". Story title: "Chicago 311 response
times". Each story point keeps the dashboard's own title and caption; the story caption is only
the short navigation label.

## 10. Check before publishing

- Hover-check one mark per dashboard against its CSV row.
- No sheet uses `SUM` or `AVG` on `median_hours`, `p90_hours` or a field built from them
  (search each sheet's Columns, Rows and Marks).
- The snapshot month (the newest `month`; November 2026 in the 2026-11-04 export) does not
  appear on any trend, and the dashed part covers the three full months before it.
- Every dashboard has the `Footer` worksheet, and it names the snapshot month.
- `Top 10 types` holds the same 10 types in `v_type_month`, `v_origin` and `areas`, and they are
  the 10 types `Panel order` names. If not, update `Trend group` and `Panel order` for
  dashboard 3 and review the Building Violation flag on dashboards 2 and 4.
- Captions match the sketch, and each still holds against its chart.

## 11. Publish and hand back

1. File > Save to Tableau Public As..., name "Chicago 311 response times". In the workbook's
   settings on Tableau Public, turn on "Allow others to download" so the `.twbx` is
   downloadable, and set the Story as the first sheet shown.
2. Save a local copy as `chicago-311-response-times.twbx` (File > Save As, if your version
   allows saving locally; otherwise download it from your Tableau Public profile).
3. Screenshot each dashboard (Dashboard > Export Image, PNG) as
   `dashboard-1-long-waits.png` to `dashboard-5-explore.png`.
4. Bring back to the repo: the `.twbx`, the five PNGs, and the Tableau Public URL. An agent
   session then commits the `.twbx` to `dashboards/tableau/`, writes
   `dashboards/tableau/README.md` with the link, puts the PNGs in `docs/img/`, and embeds them
   in `docs/findings.md`.
