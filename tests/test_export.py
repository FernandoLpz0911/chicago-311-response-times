import csv

from pipeline.export import EXPORT_VIEWS, export_views


def _read(path):
    with open(path, newline="") as f:
        return list(csv.reader(f))


def test_export_writes_one_csv_per_view_with_header(loaded, tmp_path):
    out = tmp_path / "exports"
    counts = export_views(loaded, out)
    assert counts == {
        "v_city_month": 2,
        "v_type_month": 3,
        "v_area_type": 3,
        "v_backlog": 2,
        "v_origin": 7,
        "v_area_centroid": 2,
    }
    for view in EXPORT_VIEWS:
        assert len(_read(out / f"{view}.csv")) == counts[view] + 1


def test_export_columns_and_order(loaded, tmp_path):
    export_views(loaded, tmp_path)
    rows = _read(tmp_path / "v_type_month.csv")
    assert rows[0] == ["sr_type", "month", "requests", "completed", "median_hours", "p90_hours"]
    assert [r[:2] for r in rows[1:]] == [
        ["Graffiti Removal Request", "2024-01-01"],
        ["Pothole in Street Complaint", "2024-01-01"],
        ["Pothole in Street Complaint", "2024-02-01"],
    ]


def _add_pothole_closed_after(conn, raw_rows, sr_number, closed):
    from pipeline.load import load_page

    row = dict(raw_rows[0], sr_number=sr_number, closed_date=closed)
    row["created_date"] = "2024-01-10T08:00:00.000"
    load_page(conn, [row])


def _pothole_january(path):
    return next(r for r in _read(path) if r[:2] == ["Pothole in Street Complaint", "2024-01-01"])


def test_export_can_leave_out_requests_closed_within_minutes(loaded, raw_rows, tmp_path):
    _add_pothole_closed_after(loaded, raw_rows, "SR24-00000101", "2024-01-10T08:05:59.000")
    _add_pothole_closed_after(loaded, raw_rows, "SR24-00000102", "2024-01-10T08:06:00.000")

    export_views(loaded, tmp_path / "all")
    export_views(loaded, tmp_path / "worked", min_minutes=6)

    # requests, completed: 3 fixture potholes plus both new ones, then without the 5:59 one
    assert _pothole_january(tmp_path / "all" / "v_type_month.csv")[2:4] == ["5", "5"]
    assert _pothole_january(tmp_path / "worked" / "v_type_month.csv")[2:4] == ["4", "4"]


def test_min_minutes_does_not_outlive_the_export(loaded, raw_rows, tmp_path):
    _add_pothole_closed_after(loaded, raw_rows, "SR24-00000101", "2024-01-10T08:01:00.000")
    export_views(loaded, tmp_path, min_minutes=6)
    sql = "SELECT count(*) FROM mart.v_requests_clean WHERE sr_number = 'SR24-00000101'"
    assert loaded.execute(sql).fetchone()[0] == 1
