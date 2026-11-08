# Tableau workbook sketch

What each of the five dashboards shows, so the workbook can be built from this page. Each
dashboard is one finding from [docs/findings.md](../../docs/findings.md), plus one explore page.
Layouts are rough; change them freely while building as long as the data rules below hold.

## Before you build

Follow [BUILD.md](BUILD.md): it has the checklist for uploading the exports and the boundary
file to Tableau Public's web editor, and step-by-step build notes for each dashboard and the
Story. The
exports in `exports/` already use the 6-minute rule and include `v_type_summary.csv`.

## Rules for every dashboard

**Never combine medians.** Each export row holds a median for one group (one type, one month,
one area, one channel). A median of medians, or a sum of them, is wrong. Show `median_hours`
only at the grain of the export row. In practice:

- Put `sr_type` (and `month`, `community_area` or `origin`, whatever the export is grouped by)
  on the view, so each mark is one export row.
- Use the attribute or `MIN()` aggregation for `median_hours` and `p90_hours`, not `SUM` or
  `AVG`.
- For a city-wide figure across all types, use `v_city_month`, never an aggregate of
  `v_type_month`.

**Calculated fields** (create in each data source that needs them):

| Field | Formula | Used in |
|---|---|---|
| `Median days` | `[median_hours] / 24` | all |
| `P90 days` | `[p90_hours] / 24` | 1, explore |
| `Tail ratio` | `[p90_hours] / [median_hours]` | 1 |
| `Channel` | `CASE [origin] WHEN 'Phone Call' THEN 'Phone' WHEN 'Internet' THEN 'Website' WHEN 'Mobile Device' THEN 'App' ELSE 'Other' END` | 4, explore |
| `Show month` | `[month] < {MAX([month])}` | 3, explore |
| `Provisional` | `DATEDIFF('month', [month], {MAX([month])}) <= 3` | 3, explore |

**Top 10 types.** The findings use the 10 types with the most requests after cleaning. Build it
once as a set on `sr_type` in `v_type_month`: Top 10 by `SUM([requests])`. Requests (not
medians) can be summed. The set should hold the same 10 types as findings 2 to 4; check it
against the tables there. The margin at the bottom is thin: Building Violation (10th, 75,079
requests) is only about 1,500 ahead of Tree Removal Inspection (11th), so a re-export could swap
them. Each monthly refresh checks the set ([REFRESH.md](REFRESH.md)).

**Units.** Show waits in days, one decimal (graffiti shows as 1.0 days, not 23.7 hours). One unit
across the workbook beats switching between hours and days.

**Footer on every dashboard:** a small worksheet on `v_city_month`, not a fixed text box, so the
date updates itself when the data is refreshed. Its text: "Chicago 311 service requests created
from January 2023 to <newest month>; the newest month is partial. Requests closed within 6
minutes are left out. Waits are medians of completed requests; open requests are not counted."
`<newest month>` is `MAX([month])` shown as month and year (November 2026 in the 2026-11-04
export). Plus a link to the GitHub repo.

**Captions carry no numbers.** Each caption states its pattern in words; the numbers live in the
chart and its tooltips. The dashboards are refreshed monthly ([REFRESH.md](REFRESH.md)), and a
caption without numbers stays true unless the pattern itself changes, which each refresh checks.
`docs/findings.md` keeps the numbers, pinned to the 2026-11-04 export.

**Colour.** One neutral colour (grey) for context marks and one accent colour for the marks the
caption talks about. For finding 3, one colour for slowed down and one for sped up. Use a
colour-blind-safe pair, such as Tableau's blue and orange.

## 2026 is a partial year

Settled here, for every trend chart (finding 3 and the explore page):

- **Drop the snapshot month** (the newest month, which is partial). In the 2026-11-04 export,
  November 2026 has 66 completed requests out of 1,202. `Show month`
  filters it out. Because it uses `{MAX([month])}`, it keeps working after a re-export.
- **Mark the last three full months as provisional** (August to October 2026 in this
  snapshot). Many of their requests are still open: city-wide, 81% of August requests are
  complete, 69% of September and 52% of October, against about 90% in normal months. Their
  medians will rise as those close. Draw them with a dashed line or lighter colour, using
  `Provisional` on the line's Detail and Line style. Add a shaded reference band over them,
  labelled "Still settling: many requests open".
- **No year-to-date totals presented as a full year.** Where a year label appears, mark the
  newest year as partial, for example "2026 (to Nov 1)".

Three months is a judgement call: it is where city-wide completion falls below 80%. Building
Violation settles more slowly (71% complete in August, 92% in April), which the finding 3 caption
already says.

## Dashboard 1: Long waits

**Title:** Some services help most people within days but leave one in ten waiting more than a
year

**Data:** `v_type_summary` (new, see [Data gaps](#data-gaps)).

**Chart:** dumbbell chart. One row per request type. Two dots per row: median wait and 90th
percentile wait, in days, joined by a line. Log scale on the x axis, because the waits range from
hours to over two years. Rows sorted by `Tail ratio`, highest first. Label the ratio at the
right end of each row ("59x").

**Filters:** the same rows as the finding 1 table, picked the way
[01_long_tail_types.sql](../../sql/analysis/01_long_tail_types.sql) picks them, all fixed and
hidden from the viewer: `completed >= 1000`, then the top 15 by gap (`p90_hours - median_hours`),
then `Tail ratio >= 6`. That leaves 6 rows, Bicycle Request/Complaint (59x) to Sewer Cave-In
Inspection Request (6.8x). Do not take the top 15 by `Tail ratio` instead: that puts
short-median types such as Street Light Pole Damage Complaint (7-hour median, 114x) on top, which
does not match the finding. Highlight Bicycle Request/Complaint in the accent colour.

```
Bicycle Request/Complaint        o----------------------------o  59x
Street Light On During Day         o------------------------o    27x
Water Lead Test Kit Request               o----------------o      12x
...
                                 1d     10d    100d    1000d   (log)
                                 o median   o 90th percentile
```

**Caption:** "For these types, most requests close within days or weeks, but the slowest one in
ten waits many times longer; bicycle requests have the longest tail. A long tail can come from backlog clean-ups, when a department closes many old requests on
the same day, rather than from late work. Open requests are not counted, so the real tail is
longer."

## Dashboard 2: Where you live

**Title:** Where you live changes how fast the same problem gets fixed

**Data:** `v_area_type`, joined to `community_areas.geojson` on `community_area` (integer on both
sides; all 77 areas join).

**Charts:**

1. **Map** (left, large): community areas coloured by `Median days` for one request type.
   Sequential colour, light is fast, dark is slow. Areas with fewer than 50 completed requests
   of that type are grey and labelled "Too few requests" in the tooltip. Tooltip: area name,
   median days, completed requests.
2. **Gap strip** (right): one row per top-10 type. Each area is a small grey dot on a days axis.
   The fastest and slowest areas are larger accent dots, labelled with the area name. Rows sorted
   by the ratio of slowest to fastest. Clicking a row sets the map's type.

**Filters:** request type, single-value dropdown, limited to the top 10 set. Default: Abandoned
Vehicle Complaint (the headline number). Minimum 50 completed requests per area and type, fixed.

```
+---------------------------+  Building Violation   . .. ...:: ..  .   O
|                           |  Abandoned Vehicle     O ..::. .   O
|    [map of 77 areas]      |  Pothole in Street      O.::.. O
|                           |  ...
|                           |                  0d    20d    40d    80d
+---------------------------+  O = fastest / slowest area
```

**Caption:** "The same problem can wait several times longer in one community area than in
another. The comparison takes the two extremes of 77 areas and does not account for how
many requests an area sends or how serious they are."

**Building Violation:** keep it in the strip, with a note in its tooltip: "Covers many kinds of
problem, so the gap may reflect what gets reported in each area as much as how fast it is
handled." No breakdown by sub-type; the exports have none.

## Dashboard 3: Trends

**Title:** Cart repairs and potholes have slowed down; rat baiting and building violations have
sped up

**Data:** `v_type_month`, filtered to the top 10 set.

**Chart:** small multiples, 2 rows by 5 columns, one panel per type. Each panel is a line of
`Median days` by month. Each panel has its own y axis, because the types range from under a day
to 60 days. Panels ordered: the three that slowed (Garbage Cart Maintenance, Blue Recycling Cart,
Pothole in Street Complaint) in the slowed colour, then the two that sped up (Rodent
Baiting/Rat Complaint, Building Violation) in the sped-up colour, then the rest in grey.
Provisional months dashed, as in [2026 is a partial year](#2026-is-a-partial-year).

**Filters:** `Show month` = True (fixed). No viewer filters; the explore page covers other types.

```
Garbage Cart     Blue Recycling   Pothole          Rodent Baiting   Building Viol.
   __/\_/--..      _/\__/--..       __/-\_..        \__.__..        \___..
2023      2026   ...
Tree Debris      Abandoned Veh.   Tree Emergency   Street Light     Graffiti
   grey            grey             grey             grey             grey
```

**Caption:** "Garbage cart repairs, blue recycling carts and potholes wait longer than they did in
2023; rat baiting and building violations are handled faster. Recent months are still settling: their medians will rise as open requests close. Tree
types depend on storms and seasons."

Yearly medians stay in `docs/findings.md`: they cannot be rebuilt from monthly ones, so the
dashboard does not show them.

## Dashboard 4: How you report

**Title:** How you report a problem mostly does not matter, except for building violations

**Data:** `v_origin`, filtered to the top 10 set and `Channel` in Phone, Website, App.

**Chart:** dot plot. One row per type. Three dots per row, one per channel, coloured by channel,
with a thin grey line from the fastest to the slowest. Rows sorted by the gap between the
slowest and fastest channel, largest first, so Building Violation is on top. Label the Building
Violation dots with their values.

**Filters:** none for the viewer.

```
Building Violation      W A ----------------------- P      34.8 vs 16.1 days
Pothole in Street          A P -- W
Tree Debris                W A - P
Graffiti                   WAP
...
                        P Phone   W Website   A App
```

**Caption:** "For most of the busiest types, the channel a problem is reported on makes little
difference. Building violations are the exception: phone reports wait far longer than website or
app reports. The data does not say why; phone and website
reports may describe different problems."

## Dashboard 5: Explore

**Title:** Explore 311 response times

**Data:** all six exports. `sr_type` links them (Tableau relationships or blending on
`sr_type`).

**Filters (top bar):** request type (single-value dropdown, all types, default "All types"),
community area (map click, single value), month range (slider, with `Show month` applied).

**Tiles (top row):** requests, completed, median days, open requests. With "All types",
tiles and the trend come from `v_city_month` and the backlog from all of `v_backlog`. With one
type, they come from `v_type_month` and that type's backlog. Median days is the median of the
latest full month, labelled with the month, not an aggregate over the range.

**Charts:**

1. **Trend:** median days by month (`v_city_month` or `v_type_month`), with a thin p90 line.
   Provisional months dashed.
2. **Map:** median days by community area for the selected type (`v_area_type`). Hidden or
   greyed out with "All types", since the export has no all-types row per area. Uses
   `v_area_centroid` labels for area names.
3. **By channel:** bar of median days for Phone, Website and App for the selected type
   (`v_origin`).
4. **Backlog:** bar of open requests by age bucket (`v_backlog`). Bucket labels already sort
   correctly ("1: <1 day" to "5: 90+ days").

The community area filter only applies to the map: no other export has an area column. Say so
in a small note under the filter.

```
[Type v] [Month range ======] [Area: click map]
+--------+--------+--------+--------+
|requests|complete|median d|  open  |
+--------+--------+--------+--------+
| trend line (median, p90)          |  map            |
+-----------------------------------+-----------------+
| by channel bars | backlog by age bars               |
```

**Caption:** "Medians are per type, month, area or channel; they are not added up across
groups."

## Data gaps

- **Type-level summary (needed for dashboard 1).** No export has median and 90th percentile per
  type over the whole period, and they cannot be rebuilt from `v_type_month` or `v_area_type`.
  Done: `mart.v_type_summary` (`sr_type, requests, completed, median_hours, p90_hours`, over
  all of `v_requests_clean`) is now exported as `v_type_summary.csv`.
- **Not needed:** channel by year (finding 4 says phone is slowest every year; the dashboard
  leaves that to the caption) and yearly medians by type (finding 3 uses monthly lines).
