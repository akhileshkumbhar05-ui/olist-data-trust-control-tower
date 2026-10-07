"""Native Spark parity checks against the isolated DEMO / SYNTHETIC fixture."""
import pandas as pd
import pytest
from tests.fixtures import demo_tables
from olist.quality.rules import RULES
from olist.quality.engine import evaluate
from olist.quality.spark_engine import evaluate_spark, predicate
from olist.transformations.models import standardize, gold_models
from olist.transformations.spark_models import standardize_spark, gold_spark
from olist.metrics.definitions import calculate


@pytest.fixture(scope="module")
def spark():
    from pyspark.sql import SparkSession
    session = SparkSession.builder.master("local[2]").appName("olist-test-isolated").config("spark.sql.shuffle.partitions", "2").config("spark.ui.enabled", "false").config("spark.sql.session.timeZone", "UTC").getOrCreate()
    session.sparkContext.setLogLevel("ERROR")
    yield session
    session.stop()


def frames(spark, source):
    from pyspark.sql.types import StructType, StructField, StringType
    result = {}
    for ds, df in source.items():
        columns = ["source_record_id", *df.columns]
        rows = [[str(idx), *[None if pd.isna(v) else str(v) for v in row]] for idx, row in zip(df.index, df.itertuples(index=False, name=None))]
        result[ds] = spark.createDataFrame(rows, StructType([StructField(c, StringType(), True) for c in columns])).cache()
    return result


def test_native_spark_medallion_matches_local_metrics_and_grains(spark):
    tables = demo_tables()
    s, _ = standardize(tables)
    expected = calculate(gold_models(s)["fact_orders"])
    native, cascade = standardize_spark(frames(spark, tables))
    gold = gold_spark(native)
    actual = calculate(gold["fact_orders"].toPandas())
    assert actual == expected
    assert gold["fact_orders"].count() == 3
    assert gold["fact_order_items"].count() == 3
    geo = native["geolocation"].first()
    assert geo.geolocation_lat == -23.5
    assert geo.observation_count == 2
    assert all(df.count() == 0 for _, _, df in cascade)


def test_native_quality_matches_local_control_results(spark):
    tables = demo_tables()
    tables["order_items"].loc[0, "price"] = "-1"
    tables["orders"].loc[0, "order_approved_at"] = "2018-01-01 07:00:00"
    tables["reviews"].loc[0, "review_score"] = "6"
    tables["payments"].loc[0, "order_id"] = "orphan"
    tables["products"].loc[0, "product_category_name"] = pd.NA
    ids = {"orders.schema", "orders.status", "orders.lifecycle", "orders.payment_reconciliation", "orders.unique_key", "reviews.score", "payments.fk_order_id", "products.category", "order_items.nonnegative_price", "order_items.parse_price", "order_items.required_key", "order_items.unique_key", "geolocation.geolocation_lat"}
    rules = [r for r in RULES if r.rule_id in ids]
    local = evaluate(tables, "r", "now", rules)
    results, failures, quarantine, _, accepted = evaluate_spark(frames(spark, tables), "r", "now", rules)
    assert results.set_index("rule_id").records_failed.to_dict() == local.results.set_index("rule_id").records_failed.to_dict()
    assert quarantine.count() == len(local.quarantine)
    assert accepted["order_items"].count() == len(local.accepted["order_items"])


def test_native_duplicate_and_timestamp_controls(spark):
    tables = demo_tables()
    tables["orders"] = pd.concat([tables["orders"], tables["orders"].iloc[:1]], ignore_index=True)
    tables["orders"].loc[1, "order_purchase_timestamp"] = "broken"
    tables["orders"].loc[1, "order_delivered_customer_date"] = pd.NA
    dfs = frames(spark, tables)
    for rid, expected in [("orders.unique_key", 2), ("orders.parse_order_purchase_timestamp", 1), ("orders.delivered_time", 1)]:
        rule = next(r for r in RULES if r.rule_id == rid)
        assert predicate(rule, dfs).count() == expected
