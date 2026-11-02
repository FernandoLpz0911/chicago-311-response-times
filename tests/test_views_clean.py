import pytest


def test_clean_view_drops_duplicates_info_calls_and_bad_rows(loaded):
    rows = loaded.execute("SELECT sr_number FROM mart.v_requests_clean ORDER BY 1").fetchall()
    assert [r[0] for r in rows] == [
        "SR24-00000001", "SR24-00000002", "SR24-00000003", "SR24-00000004",
        "SR24-00000005", "SR24-00000006", "SR24-00000007", "SR24-00000008",
        "SR24-00000013",
    ]


def test_response_hours_only_for_completed_requests(loaded):
    hours = dict(
        loaded.execute("SELECT sr_number, response_hours FROM mart.v_requests_clean").fetchall()
    )
    assert hours["SR24-00000001"] == pytest.approx(10)
    assert hours["SR24-00000002"] == pytest.approx(48)
    assert hours["SR24-00000007"] == pytest.approx(30)
    assert hours["SR24-00000005"] is None  # still open
    assert hours["SR24-00000013"] is None  # canceled, not completed


def test_data_issues_lists_unusable_completed_requests(loaded):
    rows = loaded.execute(
        "SELECT sr_number, reason FROM mart.v_data_issues ORDER BY sr_number"
    ).fetchall()
    assert rows == [
        ("SR24-00000011", "completed_without_closed_date"),
        ("SR24-00000012", "closed_before_created"),
    ]


def test_null_duplicate_flag_counts_as_not_duplicate(loaded):
    loaded.execute(
        "UPDATE raw.service_requests SET duplicate = NULL WHERE sr_number = 'SR24-00000001'"
    )
    row = loaded.execute(
        "SELECT 1 FROM mart.v_requests_clean WHERE sr_number = 'SR24-00000001'"
    ).fetchone()
    assert row == (1,)


@pytest.mark.parametrize(
    ("sr_type", "origin"),
    [
        ("Aircraft Noise Complaint", "Internet"),
        ("Tree Trim Request (NO LONGER BEING ACCEPTED)", "Phone Call"),
        ("Finance Parking Code Enforcement Review", "Internet"),
        ("Graffiti Removal Request", "Mass Entry"),
    ],
)
def test_clean_view_drops_record_only_requests(conn, raw_rows, sr_type, origin):
    from pipeline.load import load_page

    row = {**raw_rows[0], ":id": "row-0099", "sr_number": "SR24-00000099",
           "sr_type": sr_type, "origin": origin}
    load_page(conn, [row])
    found = conn.execute(
        "SELECT 1 FROM mart.v_requests_clean WHERE sr_number = 'SR24-00000099'"
    ).fetchone()
    assert found is None


def _add_pothole_closed_at(conn, raw_rows, sr_number, closed):
    from pipeline.load import load_page

    row = {**raw_rows[0], "sr_number": sr_number,
           "created_date": "2024-01-10T08:00:00.000", "closed_date": closed}
    load_page(conn, [row])


def _quick_closures_kept(conn):
    rows = conn.execute(
        "SELECT sr_number FROM mart.v_requests_clean WHERE sr_number LIKE 'SR24-000001%'"
    ).fetchall()
    return {r[0] for r in rows}


def test_clean_view_drops_requests_closed_within_6_minutes(loaded, raw_rows):
    _add_pothole_closed_at(loaded, raw_rows, "SR24-00000101", "2024-01-10T08:05:59.000")
    _add_pothole_closed_at(loaded, raw_rows, "SR24-00000102", "2024-01-10T08:06:00.000")
    assert _quick_closures_kept(loaded) == {"SR24-00000102"}


@pytest.mark.parametrize(
    ("min_minutes", "kept"),
    [("0", {"SR24-00000101", "SR24-00000102"}), ("", {"SR24-00000102"})],
)
def test_clean_view_cutoff_can_be_changed_per_session(loaded, raw_rows, min_minutes, kept):
    _add_pothole_closed_at(loaded, raw_rows, "SR24-00000101", "2024-01-10T08:05:59.000")
    _add_pothole_closed_at(loaded, raw_rows, "SR24-00000102", "2024-01-10T08:06:00.000")
    loaded.execute("SELECT set_config('chi311.min_minutes', %s, false)", [min_minutes])
    assert _quick_closures_kept(loaded) == kept
