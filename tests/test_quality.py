from dataclasses import replace
import pandas as pd
import pytest
from tests.fixtures import demo_tables
from olist.quality.engine import evaluate, mask_for, readiness, quality_score
from olist.quality.rules import RULES


def rule(rule_id):
    return next(r for r in RULES if r.rule_id == rule_id)


def test_clean_fixture_and_status_aware_timestamps():
    tables = demo_tables()
    q = evaluate(tables, "run", "now")
    assert readiness(q.results) == "READY"
    assert q.quarantine.empty
    assert quality_score(q.results) == 100
    assert not mask_for(rule("orders.delivered_time"), tables["orders"], tables).iloc[2]


@pytest.mark.parametrize("rule_id,dataset,column,value", [
    ("order_items.nonnegative_price", "order_items", "price", "-1"),
    ("order_items.parse_price", "order_items", "price", "oops"),
    ("reviews.score", "reviews", "review_score", "6"),
    ("order_items.fk_product_id", "order_items", "product_id", "missing"),
    ("orders.parse_order_purchase_timestamp", "orders", "order_purchase_timestamp", "invalid"),
    ("orders.delivered_time", "orders", "order_delivered_customer_date", pd.NA),
    ("geolocation.geolocation_lat", "geolocation", "geolocation_lat", "91"),
])
def test_bad_records_route_to_quarantine(rule_id, dataset, column, value):
    tables = demo_tables()
    tables[dataset].loc[0, column] = value
    q = evaluate(tables, "run", "now")
    failure = q.results[q.results.rule_id.eq(rule_id)].iloc[0]
    assert failure.records_failed == 1
    assert failure.status == "FAILED"
    assert len(q.accepted[dataset]) == len(tables[dataset]) - 1
    assert rule_id in q.quarantine.rule_id.values
    assert "original_values" in q.quarantine


def test_duplicate_and_composite_keys_quarantine_all_ambiguous_rows():
    tables = demo_tables()
    tables["order_items"] = pd.concat([tables["order_items"], tables["order_items"].iloc[:1]], ignore_index=True)
    q = evaluate(tables, "run", "now")
    assert q.results.set_index("rule_id").loc["order_items.unique_key", "records_failed"] == 2
    assert readiness(q.results) == "BLOCKED"
    assert len(q.accepted["order_items"]) == 2


def test_review_id_alone_is_not_key():
    tables = demo_tables()
    tables["reviews"].loc[2, "review_id"] = "r1"
    q = evaluate(tables, "run", "now")
    assert q.results.set_index("rule_id").loc["reviews.unique_key", "records_failed"] == 0


def test_lifecycle_is_warning_and_canceled_is_exempt():
    tables = demo_tables()
    tables["orders"].loc[0, "order_approved_at"] = "2018-01-01 07:00:00"
    tables["orders"].loc[2, "order_delivered_carrier_date"] = "2000-01-01"
    q = evaluate(tables, "run", "now")
    assert q.results.set_index("rule_id").loc["orders.lifecycle", "records_failed"] == 1
    assert readiness(q.results) == "WARNING"
    assert len(q.accepted["orders"]) == 3


def test_score_uses_opportunities_and_readiness_blocks_errors():
    results = pd.DataFrame([dict(status="PASSED", severity="HIGH", action="WARN", records_evaluated=10, records_failed=0), dict(status="FAILED", severity="HIGH", action="QUARANTINE", records_evaluated=10, records_failed=2)])
    assert quality_score(results) == 90
    assert readiness(results) == "WARNING"
    results.loc[1, "severity"] = "CRITICAL"
    assert readiness(results) == "BLOCKED"
    results.loc[1, "status"] = "SKIPPED"
    assert readiness(results) == "BLOCKED"
    assert readiness(results.iloc[:0]) == "BLOCKED"


def test_schema_drift_blocks_publication():
    tables = demo_tables()
    tables["orders"]["unexpected"] = "drift"
    q = evaluate(tables, "run", "now")
    assert readiness(q.results) == "BLOCKED"
    assert q.accepted["orders"].empty


def test_inactive_rule_is_not_scored():
    r = replace(rule("orders.status"), active_flag=False)
    q = evaluate(demo_tables(), "run", "now", [r, rule("orders.schema")])
    assert len(q.results) == 1
    assert quality_score(q.results) == 100


def test_missing_schema_fields_are_preserved_as_failed_gate_records():
    tables = demo_tables()
    tables["orders"] = tables["orders"].drop(columns="order_purchase_timestamp")
    q = evaluate(tables, "run", "now")
    assert readiness(q.results) == "BLOCKED"
    assert q.accepted["orders"].empty
    assert set(q.quarantine[q.quarantine.dataset.eq("orders")].source_record_id) == {"0", "1", "2"}
    error = q.results[q.results.rule_id.eq("orders.parse_order_purchase_timestamp")].iloc[0]
    assert error.status == "ERROR"
    assert error.records_evaluated == 0


@pytest.mark.parametrize("value", ["NaN", "inf", "-inf"])
def test_nonfinite_numeric_input_is_not_accepted(value):
    tables = demo_tables()
    tables["order_items"].loc[0, "price"] = value
    q = evaluate(tables, "run", "now")
    assert q.results.set_index("rule_id").loc["order_items.parse_price", "records_failed"] == 1
    assert len(q.accepted["order_items"]) == 2
