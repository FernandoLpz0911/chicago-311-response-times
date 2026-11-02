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
