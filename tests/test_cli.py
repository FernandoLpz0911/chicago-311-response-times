import pytest

from pipeline import cli
from pipeline.config import DEFAULT_DATABASE_URL, Settings


def test_settings_defaults(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("SOCRATA_APP_TOKEN", "")
    assert Settings.from_env() == Settings(database_url=DEFAULT_DATABASE_URL, app_token=None)


def test_requires_a_command():
    with pytest.raises(SystemExit):
        cli.main([])


def test_migrate_command(conn, database_url, monkeypatch, capsys):
    monkeypatch.setenv("DATABASE_URL", database_url)
    assert cli.main(["migrate"]) == 0
    out = capsys.readouterr().out
    assert "applied schema/002_raw_service_requests.sql" in out
    assert "applied views/010_v_requests_clean.sql" in out


def test_load_areas_command(conn, database_url, area_rows, monkeypatch, capsys):
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setattr(cli, "fetch_community_areas", lambda session, app_token: area_rows)
    assert cli.main(["load-areas"]) == 0
    assert "loaded 2 community areas" in capsys.readouterr().out
    assert conn.execute("SELECT count(*) FROM ref.community_areas").fetchone()[0] == 2


def test_load_command_passes_app_token(conn, database_url, monkeypatch, capsys):
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("SOCRATA_APP_TOKEN", "tok")
    seen = {}

    def fake_run_load(connection, session, app_token):
        seen["app_token"] = app_token
        return 1234

    monkeypatch.setattr(cli, "run_load", fake_run_load)
    assert cli.main(["load"]) == 0
    assert seen == {"app_token": "tok"}
    assert "done: 1,234 rows loaded" in capsys.readouterr().out


def test_export_command(loaded, database_url, monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("DATABASE_URL", database_url)
    assert cli.main(["export", "--out", str(tmp_path)]) == 0
    assert "v_origin: 7 rows" in capsys.readouterr().out
    assert (tmp_path / "v_city_month.csv").is_file()
