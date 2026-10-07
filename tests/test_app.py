from streamlit.testing.v1 import AppTest
from olist.config import Config
from olist.pipeline import run_local
from tests.fixtures import demo_tables


def test_all_application_pages_render_curated_pipeline_outputs(tmp_path, monkeypatch):
    tables = demo_tables()
    tables["order_items"].loc[1, "price"] = "-50"
    run_local(Config(tmp_path), data_label="DEMO / SYNTHETIC", tables=tables)
    monkeypatch.setenv("OLIST_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("OLIST_BACKEND", "local")
    app = AppTest.from_file("app/app.py", default_timeout=30).run()
    assert not app.exception
    assert app.metric[0].value == "3"
    choices = app.sidebar.radio[0].options
    assert len(choices) == 10
    for page in choices:
        app.sidebar.radio[0].set_value(page).run()
        assert not app.exception, (page, app.exception)
        assert not app.error, (page, app.error)


def test_app_discloses_blocked_latest_attempt(tmp_path, monkeypatch):
    import pandas as pd
    run_local(Config(tmp_path), tables=demo_tables(), data_label="DEMO / SYNTHETIC")
    tables = demo_tables()
    tables["orders"] = pd.concat([tables["orders"], tables["orders"].iloc[:1]], ignore_index=True)
    run_local(Config(tmp_path), tables=tables, data_label="DEMO / SYNTHETIC")
    monkeypatch.setenv("OLIST_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("OLIST_BACKEND", "local")
    app = AppTest.from_file("app/app.py", default_timeout=30).run()
    app.sidebar.button[0].click().run()
    assert not app.exception
    assert any("BLOCKED" in e.value and "previous" in e.value for e in app.error)
