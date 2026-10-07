"""Cumulative chronological simulation; reruns never append duplicate business facts."""
from datetime import datetime, timezone
from pathlib import Path
import json
import uuid
import pandas as pd
from olist.config import Config
from olist.ingestion.catalog import SOURCES
from olist.ingestion.acquire import read_sources
from olist.quality.engine import evaluate, readiness, quality_score, FAILURE_COLUMNS
from olist.quality.rules import RULES
from olist.transformations.models import standardize, gold_models
from olist.metrics.definitions import calculate, definitions_frame
from olist.governance.catalog import table_catalog, lineage_catalog
from olist.observability.store import LocalStore


def select_cohort(tables, batch_end=None):
    selected = {name: df.copy() for name, df in tables.items()}
    if batch_end:
        end = pd.Timestamp(batch_end)
        if pd.isna(end):
            raise ValueError("Invalid batch end")
        date = pd.to_datetime(selected["orders"].order_purchase_timestamp, errors="coerce", format="mixed")
        # Keep unparseable source dates visible to quality rules, never silently discard.
        selected["orders"] = selected["orders"][date.lt(end) | date.isna()]
        ids = selected["orders"].order_id
        for name in ("order_items", "payments", "reviews"):
            # True source orphans stay visible; future valid order children are deferred.
            source_order_ids = tables["orders"].order_id
            s = selected[name].order_id
            selected[name] = selected[name][s.isin(ids) | ~s.isin(source_order_ids)]
    return selected


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def run_local(config: Config, batch_end=None, data_label="REAL OLIST", tables=None):
    started = utcnow()
    run_id = uuid.uuid4().hex
    store = LocalStore(config.root)
    audit = {"run_id": run_id, "status": "RUNNING", "started_at": started,
             "batch_start": "source inception", "batch_end": batch_end or "full historical snapshot",
             "data_label": data_label, "records_received": 0, "records_processed": 0,
             "accepted_records": 0, "quarantined_records": 0, "failed_checks": 0,
             "error_message": "", "latest_source_event": None}
    store.audit(audit)
    try:
        source = tables if tables is not None else read_sources(config.root / "raw")
        selected = select_cohort(source, batch_end)
        # Source row identity includes dataset and original CSV record ordinal. Unique even for duplicates.
        for name, frame in selected.items():
            frame.index = pd.Index([f"{name}:{i}" for i in frame.index], name="source_record_id")
            bronze = frame.copy()
            bronze["source_record_id"] = bronze.index
            bronze["source_file"] = SOURCES[name].filename
            bronze["pipeline_run_id"] = run_id
            bronze["ingestion_timestamp"] = started
            bronze["simulated_batch_id"] = batch_end or "full"
            bronze["simulated_batch_start"] = "source inception"
            bronze["simulated_batch_end"] = batch_end or "full"
            store.write("bronze", name, bronze, run_id)
        audit["records_received"] = sum(map(len, selected.values()))
        q = evaluate(selected, run_id, started)
        audit["records_processed"] = audit["records_received"]
        audit["failed_checks"] = int(q.results.status.eq("FAILED").sum())
        silver, cascades = standardize(q.accepted) if readiness(q.results) != "BLOCKED" else ({}, [])
        additional = pd.DataFrame([{"run_id": run_id, "dataset": ds, "source_record_id": idx,
                                    "rule_id": f"{ds}.accepted_parent", "rule_name": "Accepted parent integrity",
                                    "severity": "HIGH", "action": "QUARANTINE", "failure_reason": reason,
                                    "quarantine_timestamp": started,
                                    "original_values": json.dumps(selected[ds].loc[idx].dropna().to_dict(), default=str)}
                                   for ds, idx, reason, row in cascades], columns=FAILURE_COLUMNS)
        q.failures = pd.concat([q.failures, additional], ignore_index=True)
        q.quarantine = pd.concat([q.quarantine, additional], ignore_index=True)
        for ds, count in additional.groupby("dataset").size().items():
            mask = q.scorecard.dataset.eq(ds)
            q.scorecard.loc[mask, "accepted_records"] -= count
            q.scorecard.loc[mask, "quarantined_records"] += count
            q.scorecard.loc[mask & q.scorecard.readiness.eq("READY"), "readiness"] = "WARNING"
        unique_quarantine = q.quarantine.drop_duplicates(["dataset", "source_record_id"])
        audit["quarantined_records"] = len(unique_quarantine)
        audit["accepted_records"] = audit["records_received"] - len(unique_quarantine)
        state = readiness(q.results)
        if cascades and state == "READY":
            state = "WARNING"
        summary = {"run_id": run_id, "readiness": state, "quality_score": quality_score(q.results),
                   "quarantined_records": len(unique_quarantine), "failed_rules": audit["failed_checks"],
                   "data_label": data_label, "execution_timestamp": started,
                   "critical_failures": int(((q.results.severity == "CRITICAL") & (q.results.status == "FAILED")).sum())}
        for name, frame in {"dq_rules": pd.DataFrame([r.record() for r in RULES]), "dq_rule_results": q.results,
                             "dq_failed_records": q.failures, "quarantine": q.quarantine,
                             "dq_dataset_scorecard": q.scorecard, "dq_run_summary": pd.DataFrame([summary]),
                             "table_catalog": table_catalog(), "metric_dictionary": definitions_frame(),
                             "lineage_edges": lineage_catalog()}.items():
            store.write("quality", name, frame, run_id)
        if state == "BLOCKED":
            audit["status"] = "BLOCKED"
            audit["error_message"] = "Required quality gates failed; no Gold published. Inspect this run's rule results."
        else:
            for name, frame in silver.items():
                store.write("silver", name, frame, run_id)
            gold = gold_models(silver)
            for name, frame in gold.items():
                store.write("gold", name, frame, run_id)
            metrics = calculate(gold["fact_orders"])
            store.write("gold", "metric_values", pd.DataFrame([{"metric_id": k, "value": v, "run_id": run_id} for k, v in metrics.items()]), run_id)
            audit["status"] = "SUCCEEDED"
            event = pd.to_datetime(silver["orders"].order_purchase_timestamp, errors="coerce").max()
            audit["latest_source_event"] = str(event)
            store.publish(run_id)
    except Exception as exc:
        audit["status"] = "FAILED"
        audit["error_message"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        audit["ended_at"] = utcnow()
        audit["duration_seconds"] = (pd.Timestamp(audit["ended_at"]) - pd.Timestamp(started)).total_seconds()
        store.audit(audit)
    return audit
