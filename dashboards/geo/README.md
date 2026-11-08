# Community area boundaries

`community_areas.geojson` holds the 77 Chicago community area polygons, for filled maps in
Tableau and Power BI.

## Fields

| Field | Type | Joins to |
|-------|------|----------|
| `community_area` | integer, 1–77 | `community_area` in every export that has it, such as `v_area_centroid.csv` and `v_area_type.csv` |
| `area_name` | text, upper case | `area_name` in `v_area_centroid.csv` (names match for all 77 areas) |

Coordinates are WGS 84 longitude and latitude (the GeoJSON default), as MultiPolygons.

## Source

[Boundaries - Community Areas](https://data.cityofchicago.org/d/igwz-8jzy) on the Chicago Data
Portal (dataset `igwz-8jzy`, last updated 2025-04-22), downloaded 2026-11-03 from:

```
https://data.cityofchicago.org/api/geospatial/igwz-8jzy?method=export&format=GeoJSON
```

Changes from the portal file, to make the join work without type conversions:

- `area_numbe` (a string) became `community_area` (an integer), and `community` became
  `area_name`. The other properties (`area_num_1`, `shape_area`, `shape_len`) were dropped.
- Features are sorted by `community_area`, and coordinates are rounded to 6 decimal places
  (about 0.1 m), which roughly halves the file size.

## Using it in Tableau

Upload the file as a spatial file (in Tableau Public's web editor, or **Connect > To a File >
Spatial file** in Tableau Desktop), then add the export CSV as a second connection and relate
or join the two on `community_area`. Both sides are whole numbers, so the join works as is.
