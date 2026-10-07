from pathlib import Path
import json
import pandas as pd
import pytest
from tests.fixtures import demo_tables
from olist.config import Config
from olist.pipeline import run_local, select_cohort
from olist.observability.store import LocalStore
from olist.ingestion.acquire import land, verify_raw, read_sources
from olist.ingestion.catalog import SOURCES
from olist.ingestion.profile import profile
from app.services.data import DataService


def test_ingestion_checksum_idempotency_and_source_fidelity(tmp_path):
    source, raw = tmp_path / "input", tmp_path / "raw"
    source.mkdir()
    for ds, table in demo_tables().items():
        table.to_csv(source / SOURCES[ds].filename, index=False)
    first = land(raw, source)
    assert land(raw, source) == first
    assert read_sources(raw)["customers"].iloc[0].customer_zip_code_prefix == "01000"
    path = raw / SOURCES["orders"].filename
    path.write_text(path.read_text() + "corruption")
    with pytest.raises(ValueError, match="checksum"):
        verify_raw(raw)


def test_full_pipeline_rerun_and_audit_reconciliation(tmp_path):
    config = Config(tmp_path)
    a = run_local(config, tables=demo_tables(), data_label="DEMO / SYNTHETIC")
    b = run_local(config, tables=demo_tables(), data_label="DEMO / SYNTHETIC")
    store = LocalStore(tmp_path)
    assert a["status"] == b["status"] == "SUCCEEDED"
    assert a["run_id"] != b["run_id"]
    assert len(store.read("gold", "fact_orders")) == 3
    assert len(store.audits()) == 2
    assert b["records_received"] == b["accepted_records"] + b["quarantined_records"]
    assert store.current() == b["run_id"]


def test_blocked_attempt_preserves_previous_publication(tmp_path):
    config = Config(tmp_path)
    a = run_local(config, tables=demo_tables())
    tables = demo_tables()
    tables["orders"] = pd.concat([tables["orders"], tables["orders"].iloc[:1]], ignore_index=True)
    blocked = run_local(config, tables=tables)
    store = LocalStore(tmp_path)
    assert blocked["status"] == "BLOCKED"
    assert store.current() == a["run_id"]
    assert not (tmp_path / "runs" / blocked["run_id"] / "gold").exists()
    assert len(store.read("quality", "dq_rule_results", blocked["run_id"])) > 0


def test_pipeline_failure_is_audited(tmp_path):
    with pytest.raises(FileNotFoundError):
        run_local(Config(tmp_path))
    audit = LocalStore(tmp_path).audits().iloc[0]
    assert audit.status == "FAILED"
    assert "FileNotFoundError" in audit.error_message
    assert audit.ended_at


def test_cohort_keeps_orphans_for_quality_and_defers_future_children():
    tables = demo_tables()
    tables["payments"].loc[3] = ["orphan", "1", "voucher", "1", "5"]
    batch = select_cohort(tables, "2018-02-01")
    assert batch["orders"].order_id.tolist() == ["o1"]
    assert set(batch["payments"].order_id) == {"o1", "orphan"}


def test_profile_every_source(tmp_path):
    report = profile(demo_tables(), tmp_path)
    assert len(report["datasets"]) == 9
    assert report["cardinality_findings"]["orders_with_multiple_payments"] == 1
    assert report["cardinality_findings"]["orders_with_multiple_reviews"] == 1
    assert (tmp_path / "DATA_PROFILE.md").exists()


def test_services_only_curated_data_and_filter_cohort(tmp_path, monkeypatch):
    run_local(Config(tmp_path), tables=demo_tables())
    monkeypatch.setenv("OLIST_BACKEND", "local")
    service = DataService(Config(tmp_path))
    assert service.metrics()["gmv"] == 350
    assert service.metrics(start="2018-02-01")["gmv"] == 200
    assert service.metrics(seller="s2")["total_orders"] == 1
    assert service.metrics(category="bed_bath_table")["total_orders"] == 2
    with pytest.raises(ValueError):
        service.table("orders")
    with pytest.raises(ValueError):
        Config(catalog="unsafe; DROP")
