import pandas as pd
import pytest
from tests.fixtures import demo_tables
from olist.quality.engine import evaluate
from olist.transformations.models import standardize, gold_models, assert_grain
from olist.metrics.definitions import calculate, segment_performance


def facts():
    s, cascade = standardize(evaluate(demo_tables(), "run", "now").accepted)
    return s, gold_models(s)


def test_child_aggregation_preserves_order_grain_and_financial_totals():
    _, g = facts()
    fact = g["fact_orders"].set_index("order_id")
    assert len(fact) == 3
    assert fact.loc["o1", "item_gmv"] == 150
    assert fact.loc["o1", "payment_total"] == 165
    assert fact.loc["o1", "review_score"] == 2
    assert fact.loc["o1", "seller_count"] == 2
    assert len(g["fact_order_items"]) == 3


def test_geolocation_canonicalization_and_zip_preservation():
    silver, _ = facts()
    geo = silver["geolocation"]
    assert len(geo) == 1
    assert geo.iloc[0].geolocation_zip_code_prefix == "01000"
    assert geo.iloc[0].geolocation_lat == -23.5
    assert geo.iloc[0].observation_count == 2


def test_cascade_keeps_children_out_of_facts_and_is_auditable():
    tables = demo_tables()
    tables["products"].loc[0, "product_weight_g"] = "-5"
    q = evaluate(tables, "run", "now")
    silver, cascades = standardize(q.accepted)
    assert silver["order_items"].empty
    assert len(cascades) == 3
    assert len(gold_models(silver)["fact_orders"]) == 3


def test_metrics_expected_values_and_date_level_delivery_deadline():
    _, g = facts()
    m = calculate(g["fact_orders"])
    assert m["total_orders"] == 3
    assert m["delivered_orders"] == 2
    assert m["cancelled_orders"] == 1
    assert m["gmv"] == 350
    assert m["freight"] == 35
    assert m["aov"] == 175
    assert m["late_rate"] == 50
    assert m["on_time_rate"] == 50
    assert m["negative_review_rate"] == 50
    assert m["review_score"] == 3.5
    assert m["repeat_customer_rate"] == 100
    assert m["delay_days"] == 1


def test_segment_counts_orders_not_item_rows():
    _, g = facts()
    rank = segment_performance(g["fact_order_items"], "category")
    assert rank.iloc[0].orders == 2
    assert rank.iloc[0].late_orders == 1
    assert rank.iloc[0].delivered_gmv == 350


def test_zero_denominators_are_unavailable_not_zero():
    _, g = facts()
    m = calculate(g["fact_orders"].iloc[:0])
    assert m["total_orders"] == 0
    assert m["on_time_rate"] is None
    assert m["review_score"] is None


def test_assert_grain_catches_fanout():
    with pytest.raises(ValueError):
        assert_grain(pd.DataFrame({"id": [1, 1]}), ["id"])
