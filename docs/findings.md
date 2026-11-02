# Findings

What the 311 data says about how long Chicagoans wait for city services, and whether that wait
depends on what they report, where they live, or how they report it.

**Data.** Every 311 service request created from 2023-01-01 to 2026-11-01 on the
[Chicago Data Portal](https://data.cityofchicago.org/d/v6vf-nfxy): 7,462,885 rows. After the
[cleaning rules](../README.md#cleaning-rules) drop duplicates and record-only requests, 2,847,317
requests remain, and 2,575,211 of them are completed with a usable response time.

**Response time** is `closed_date - created_date` for completed requests. All figures are
medians unless stated, because a few requests that stay open for years would distort a mean.

**Caveats that apply to every finding:**

- Requests that are still open have no response time, so they are left out. The slowest requests
  are the most likely to still be open, which makes recent medians look faster than they will
  be once those requests close. 2026 is also a partial year.
- About 4% of completed requests (99,512) still close within 6 minutes of being opened. The city
  does not say why; a likely cause is a call taker closing a report because a work order for the
  same problem already exists. These are kept in the data. Where they change a finding, the
  finding says so.

## 1. Some services help most people within days but leave one in ten waiting more than a year

For the request types below, the median wait is reasonable, but the slowest 10% wait many times
longer. The table shows the types with the largest gap between the 90th percentile and the median
(types with at least 1,000 completed requests).

| Request type | Median wait | 90th percentile wait | Ratio |
|---|---|---|---|
| Bicycle Request/Complaint | 8.3 days | 502 days | 60.6x |
| Street Light On During Day Complaint | 10.1 days | 279 days | 27.6x |
| Water Lead Test Kit Request | 73 days | 863 days | 11.8x |
| No Building Permit and Construction Violation | 58 days | 605 days | 10.4x |
| Alley Pothole Complaint | 15.8 days | 139 days | 8.8x |
| Sewer Cave-In Inspection Request | 22 days | 154 days | 7.0x |

**Number:** half of bicycle requests close within 8.3 days, but one in ten takes more than
502 days.

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
| Pothole in Street Complaint | Near South Side | 0.9 days | North Lawndale | 15.8 days | 17.2x |
| Tree Debris Clean-Up Request | Douglas | 1.3 days | West Pullman | 11.1 days | 8.7x |
| Abandoned Vehicle Complaint | Loop | 2.6 days | Lincoln Park | 18.0 days | 6.8x |
| Tree Emergency | Near South Side | 11.5 hours | Clearing | 49.2 hours | 4.3x |
| Rodent Baiting/Rat Complaint | Loop | 2.5 days | O'Hare | 6.9 days | 2.8x |
| Graffiti Removal Request | Montclare | 15.7 hours | North Park | 30.2 hours | 1.9x |

**Number:** an abandoned vehicle reported in Lincoln Park waits a median of 18 days; in the Loop,
2.6 days.

**SQL:** [sql/analysis/02_area_gap_within_type.sql](../sql/analysis/02_area_gap_within_type.sql)

**Caveat:** the pothole gap is inflated by instant closures, which are more common in some areas
(41% of pothole requests in the Loop close within 6 minutes, against 22% on average across areas).
Leaving those out, the pothole gap shrinks to 6.0x: 3.9 days in Lincoln Square against 23 days in
Hermosa. The abandoned vehicle, rodent, and garbage cart gaps do not change, because those types
have no instant closures. The comparison picks the two extremes out of 77 areas and does not
account for how many requests an area sends or how serious they are.

## 3. Cart repairs and potholes have slowed down; rat baiting has sped up

Median response time by year of request for the 10 most-requested types:

| Request type | 2023 | 2024 | 2025 | 2026 (to Nov 1) |
|---|---|---|---|---|
| Garbage Cart Maintenance | 15.2 days | 12.4 days | 23.8 days | 30.4 days |
| Blue Recycling Cart | 22.5 days | 16.2 days | 35.1 days | 35.8 days |
| Pothole in Street Complaint | 3.8 days | 4.5 days | 7.0 days | 6.9 days |
| Tree Debris Clean-Up Request | 2.8 days | 5.9 days | 9.1 days | 7.1 days |
| Abandoned Vehicle Complaint | 8.8 days | 11.5 days | 10.7 days | 11.5 days |
| Tree Emergency | 14.2 hours | 20.8 hours | 20.1 hours | 39.0 hours |
| Rodent Baiting/Rat Complaint | 6.7 days | 4.0 days | 3.7 days | 4.5 days |
| Street Light Out Complaint | 2.7 days | 2.7 days | 2.1 days | 2.7 days |
| Traffic Signal Out Complaint | 4.3 hours | 3.5 hours | 2.2 hours | 2.7 hours |
| Graffiti Removal Request | 23.5 hours | 23.6 hours | 23.4 hours | 22.8 hours |

**Number:** the median wait for a garbage cart repair doubled, from 15 days for 2023 requests to
30 days for 2026 requests. Rat baiting went the other way, from 6.7 days to 4.5 days.

**SQL:** [sql/analysis/03_yoy_top_types.sql](../sql/analysis/03_yoy_top_types.sql)

**Caveat:** 2026 requests that are still open are not counted, so the 2026 medians are likely to
rise as those requests close. The slowdowns shown for 2026 are therefore, if anything,
understated. Tree types are seasonal and depend on storms, so one partial year can move them a
lot.

## 4. How you report a problem mostly does not matter

The query compares the median response by intake channel (phone, website, mobile app) within each
of the 10 most-requested types, so the mix of request types on each channel does not decide the
answer.

For 7 of the 10 types, the fastest and slowest channel are within 15% of each other. For
example, graffiti removal takes 22.7 hours by website, 23.7 by app, and 24.0 by phone.

The apparent exception is potholes: 2.0 days by phone against 7.8 days by app and 10.2 days by
website. But 41% of pothole reports made by phone close within 6 minutes. Leaving those out,
phone reports take 7.9 days, the same as the app. Website reports are still the slowest at 10.2
days.

**Number:** a pothole reported by phone and one reported in the app wait about the same, 7.9 and
7.8 days, once instant closures are left out.

**SQL:** [sql/analysis/04_origin_effect.sql](../sql/analysis/04_origin_effect.sql)

**Caveat:** the SQL file's pothole numbers include the instant closures; the 7.9-day figure comes
from the same query with requests closed within 6 minutes left out. Traffic signal outages and
tree emergencies also differ by channel by more than 15%, but by hours, not days.
