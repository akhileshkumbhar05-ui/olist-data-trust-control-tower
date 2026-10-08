from streamlit.testing.v1 import AppTest
from streamlit.runtime.pages_manager import PagesManager
from olist.config import Config
from olist.pipeline import run_local
from tests.fixtures import demo_tables


def test_all_application_views_render_without_duplicate_navigation_or_deprecations(tmp_path, monkeypatch, caplog):
    tables = demo_tables()
    tables["order_items"].loc[1, "price"] = "-50"
    run_local(Config(tmp_path), data_label="DEMO / SYNTHETIC", tables=tables)
    # Two runs exercise both the failure chart and quality-history chart.
    run_local(Config(tmp_path), data_label="DEMO / SYNTHETIC", tables=tables)
    monkeypatch.setenv("OLIST_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("OLIST_BACKEND", "local")
    app = AppTest.from_file("app/app.py", default_timeout=30).run()
    assert not app.exception
    assert app.metric[0].value == "3"
    choices = app.sidebar.radio[0].options
    assert choices == [
        "Executive Overview", "Operations Command Center", "Data Quality Command Center",
        "Quality Incident Detail", "Quarantine Explorer", "Data Governance",
        "Metric Dictionary", "Lineage / Trust", "Pipeline Health", "About / Methodology",
    ]
    # Verify the actual runtime discovery flag, not just the custom menu labels.
    assert PagesManager.uses_pages_directory is False
    assert len(app.sidebar.radio) == 1
    assert app.sidebar.radio[0].label == "Explore"
    for page in choices:
        app.sidebar.radio[0].set_value(page).run()
        assert not app.exception, (page, app.exception)
        assert not app.error, (page, app.error)
        assert not any("deprecat" in warning.value.lower() for warning in app.warning), page
        # Business quality warnings must remain visible.
        assert any("Data product: WARNING" in warning.value for warning in app.warning), page
        expected_charts = {"Executive Overview": 1, "Data Quality Command Center": 2}.get(page, 0)
        assert len(app.get("plotly_chart")) == expected_charts
    assert not any(record.name == "streamlit.deprecation_util" for record in caplog.records)


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
