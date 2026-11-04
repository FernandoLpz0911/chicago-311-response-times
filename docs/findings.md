# Findings

What the 311 data says about how long Chicagoans wait for city services, and whether that wait
depends on what they report, where they live, or how they report it.

**Data.** Every 311 service request created from 2023-01-01 to 2026-11-01 on the
[Chicago Data Portal](https://data.cityofchicago.org/d/v6vf-nfxy): 7,463,551 rows. After the
[cleaning rules](../README.md#cleaning-rules) drop duplicates, record-only requests, and instant
closures, 2,747,930 requests remain, and 2,475,704 of them are completed with a usable response
time.

**Pinned.** These findings, their numbers and their screenshots come from the 2026-11-04 export
and are rerun only by choice. The live dashboards on Tableau Public are refreshed monthly
([REFRESH.md](../dashboards/tableau/REFRESH.md)), so they may be newer and differ.

**Response time** is `closed_date - created_date` for completed requests. All figures are
medians unless stated, because a few requests that stay open for years would distort a mean.

**Caveats that apply to every finding:**

- Requests that are still open have no response time, so they are left out. The slowest requests
  are the most likely to still be open, which makes recent medians look faster than they will
  be once those requests close. 2026 is also a partial year.
- Requests closed within 6 minutes of being opened ("instant closures") are left out: 99,516
  requests, 3.9% of those completed. The city does not say why they close so fast; a likely cause
  is a call taker closing a report because a work order for the same problem already exists.
  They are most common for traffic signal outages (about 28% of completed requests) and potholes
  (about 22%). Keeping them would put Traffic Signal Out Complaint among the 10 most-requested
  types in place of Building Violation, and would make potholes reported by phone look about four
  times faster than they are. To rerun any query with them kept, run
  `SET chi311.min_minutes = 0` first.

## 1. Some services help most people within days but leave one in ten waiting more than a year

For the request types below, the median wait is reasonable, but the slowest 10% wait many times
longer. The table shows the types with the largest gap between the 90th percentile and the median
(types with at least 1,000 completed requests).

| Request type | Median wait | 90th percentile wait | Ratio |
|---|---|---|---|
| Bicycle Request/Complaint | 8.5 days | 503 days | 59.0x |
| Street Light On During Day Complaint | 10.2 days | 279 days | 27.3x |
| Water Lead Test Kit Request | 73 days | 863 days | 11.8x |
| No Building Permit and Construction Violation | 58 days | 605 days | 10.4x |
| Alley Pothole Complaint | 19.1 days | 144 days | 7.6x |
| Sewer Cave-In Inspection Request | 23 days | 154 days | 6.8x |

**Number:** half of bicycle requests close within 8.5 days, but one in ten takes more than
503 days.

**SQL:** [sql/analysis/01_long_tail_types.sql](../sql/analysis/01_long_tail_types.sql)

**Caveat:** a long tail can come from backlog clean-ups, where a department closes many old
requests on the same day, rather than from work done late. The data does not separate the two.
Because open requests are excluded, the real tail is longer than shown.

## 2. Where you live changes how fast the same problem gets fixed

For each of the 10 most-requested types, the query compares the community area with the
fastest median response to the one with the slowest (areas with at least 50 completed requests
of that type).

| Request type | Fastest area | Median | Slowest area | Median | Ratio |
|---|---|---|---|---|---|
| Building Violation | East Side | 3.0 days | Belmont Cragin | 83 days | 27.6x |
| Abandoned Vehicle Complaint | Loop | 2.7 days | Lincoln Park | 18.0 days | 6.8x |
| Pothole in Street Complaint | Lincoln Square | 3.9 days | Hermosa | 23.0 days | 6.0x |
| Tree Debris Clean-Up Request | Kenwood | 2.6 days | Englewood | 12.0 days | 4.5x |
| Tree Emergency | Near South Side | 12.1 hours | Clearing | 50.5 hours | 4.2x |
| Street Light Out Complaint | Lower West Side | 1.9 days | Loop | 5.5 days | 3.0x |
| Rodent Baiting/Rat Complaint | Loop | 2.5 days | O'Hare | 6.9 days | 2.8x |
| Garbage Cart Maintenance | O'Hare | 13.4 days | Rogers Park | 24.8 days | 1.9x |
| Blue Recycling Cart | Hegewisch | 19.8 days | Near West Side | 34.7 days | 1.8x |
| Graffiti Removal Request | Montclare | 17.3 hours | North Park | 30.2 hours | 1.7x |

**Number:** an abandoned vehicle reported in Lincoln Park waits a median of 18 days; in the Loop,
2.7 days.

**SQL:** [sql/analysis/02_area_gap_within_type.sql](../sql/analysis/02_area_gap_within_type.sql)

**Caveat:** the comparison picks the two extremes out of 77 areas and does not account for how
many requests an area sends or how serious they are. Building Violation has the widest gap, but
it covers many different kinds of problem, so the gap may reflect what gets reported in each
area as much as how fast it is handled.

## 3. Cart repairs and potholes have slowed down; rat baiting and building violations have sped up

Median response time by year of request for the 10 most-requested types:

| Request type | 2023 | 2024 | 2025 | 2026 (to Nov 1) |
|---|---|---|---|---|
| Garbage Cart Maintenance | 15.5 days | 12.5 days | 23.8 days | 30.5 days |
| Blue Recycling Cart | 22.6 days | 16.4 days | 35.1 days | 35.9 days |
| Pothole in Street Complaint | 6.5 days | 7.1 days | 12.8 days | 9.7 days |
| Tree Debris Clean-Up Request | 2.8 days | 6.0 days | 9.2 days | 9.0 days |
| Abandoned Vehicle Complaint | 8.8 days | 11.5 days | 10.8 days | 11.7 days |
| Tree Emergency | 15.3 hours | 21.5 hours | 20.7 hours | 41.0 hours |
| Rodent Baiting/Rat Complaint | 6.8 days | 4.0 days | 3.7 days | 4.5 days |
| Building Violation | 62 days | 41 days | 22 days | 12.2 days |
| Street Light Out Complaint | 3.0 days | 2.8 days | 2.4 days | 2.7 days |
| Graffiti Removal Request | 23.5 hours | 23.7 hours | 23.4 hours | 22.8 hours |

**Number:** the median wait for a garbage cart repair doubled, from 15.5 days for 2023 requests
to 30.5 days for 2026 requests. Rat baiting went the other way, from 6.8 days to 4.5 days, and
building violations from 62 days to 22 days between 2023 and 2025.

**SQL:** [sql/analysis/03_yoy_top_types.sql](../sql/analysis/03_yoy_top_types.sql)

**Caveat:** 2026 requests that are still open are not counted, so the 2026 medians are likely to
rise as those requests close. The slowdowns shown for 2026 are therefore, if anything,
understated, and the 2026 building violation figure is the least reliable: about a fifth of
2026 building violations are still open. The 2023 to 2025 building violation trend does not
have this problem, because nearly all of those requests are closed. Tree types are seasonal and
depend on storms, so one partial year can move them a lot.

## 4. How you report a problem mostly does not matter, except for building violations

The query compares the median response by intake channel (phone, website, mobile app) within each
of the 10 most-requested types, so the mix of request types on each channel does not decide the
answer.

For 6 of the 10 types, the fastest and slowest channel are within 15% of each other. For
example, graffiti removal takes 22.7 hours by website, 23.8 by app, and 24.0 by phone.

Building violations are the clear exception: 34.8 days by phone against 16.1 days by website and
16.3 days by app. Phone reports are the slowest in every year from 2023 to 2026. The other
exceptions are smaller. Potholes take 10.2 days by website against 7.9 by phone and 7.8 by app.
Tree debris takes 7.0 days by phone against 5.9 by website or app. Tree emergencies differ by
hours, not days.

**Number:** a building violation reported by phone waits a median of 34.8 days, more than twice
the 16.1 days for one reported on the website.

**SQL:** [sql/analysis/04_origin_effect.sql](../sql/analysis/04_origin_effect.sql)

**Caveat:** the data does not say why phone reports of building violations are slower. Because
the type covers many kinds of problem, phone and website reports may describe different
problems, which would mean the channel is not the cause.
