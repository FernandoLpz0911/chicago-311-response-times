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
