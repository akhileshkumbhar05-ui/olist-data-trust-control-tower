"""Deterministic medallion models. Independent child aggregates avoid fanout."""
import pandas as pd
from olist.ingestion.catalog import SOURCES


def standardize(tables):
    silver = {}
    for name, original in tables.items():
        df = original.copy()
        for col in SOURCES[name].numeric:
            df[col] = pd.to_numeric(df[col], errors="raise").astype(float)
        for col in SOURCES[name].timestamps:
            df[col] = pd.to_datetime(df[col], errors="raise", format="mixed")
        silver[name] = df
    # Parent removal cannot leave accepted orphaned children in business facts.
    dependencies = [("orders", "customer_id", "customers", "customer_id"),
                    ("order_items", "order_id", "orders", "order_id"),
                    ("order_items", "product_id", "products", "product_id"),
                    ("order_items", "seller_id", "sellers", "seller_id"),
                    ("payments", "order_id", "orders", "order_id"),
                    ("reviews", "order_id", "orders", "order_id")]
    # Exclusion is explicitly audited by pipeline as downstream dependency quarantine.
    cascade = []
    for child, fk, parent, pk in dependencies:
        df = silver[child]
        bad = ~df[fk].isin(silver[parent][pk])
        for idx, row in df[bad].iterrows():
            cascade.append((child, str(idx), f"Accepted parent missing: {parent}.{pk}", row))
        silver[child] = df[~bad].copy()
    geo = silver["geolocation"]
    # One canonical coordinate per ZIP. Median coordinates; deterministic modal state/city.
    def mode(s):
        counts = s.dropna().value_counts()
        return sorted(counts[counts == counts.max()].index)[0] if len(counts) else None
    silver["geolocation"] = geo.groupby("geolocation_zip_code_prefix", as_index=False).agg(
        geolocation_lat=("geolocation_lat", "median"), geolocation_lng=("geolocation_lng", "median"),
        geolocation_city=("geolocation_city", mode), geolocation_state=("geolocation_state", mode),
        observation_count=("geolocation_zip_code_prefix", "size"))
    return silver, cascade


def assert_grain(df, keys):
    if df[keys].isna().any().any() or df.duplicated(keys).any():
        raise ValueError(f"Broken grain: {keys}")


def gold_models(silver):
    orders = silver["orders"].copy()
    assert_grain(orders, ["order_id"])
    items = silver["order_items"]
    i = items.groupby("order_id", as_index=False).agg(item_gmv=("price", "sum"), freight_value=("freight_value", "sum"), item_count=("order_item_id", "size"), seller_count=("seller_id", "nunique"))
    p = silver["payments"].groupby("order_id", as_index=False).agg(payment_total=("payment_value", "sum"), payment_count=("payment_sequential", "size"))
    # Latest answered review; review_id is a stable tie-breaker.
    r = silver["reviews"].sort_values(["review_answer_timestamp", "review_id"], na_position="first").drop_duplicates("order_id", keep="last")[["order_id", "review_score"]]
    customers = silver["customers"][["customer_id", "customer_unique_id", "customer_state"]]
    fact = orders.merge(customers, on="customer_id", how="left", validate="many_to_one")
    for child in (i, p, r):
        fact = fact.merge(child, on="order_id", how="left", validate="one_to_one")
    if len(fact) != len(orders):
        raise ValueError("Order fact row-count mismatch")
    assert_grain(fact, ["order_id"])
    fact["purchase_date"] = fact.order_purchase_timestamp.dt.date.astype(str)
    delivered = fact.order_status.eq("delivered")
    fact["delivery_eligible"] = delivered & fact.order_delivered_customer_date.notna() & fact.order_estimated_delivery_date.notna()
    # Compare calendar days; midnight estimates should not label same-day arrivals late.
    fact["is_late"] = fact.delivery_eligible & (fact.order_delivered_customer_date.dt.normalize() > fact.order_estimated_delivery_date.dt.normalize())
    fact["delivery_days"] = (fact.order_delivered_customer_date - fact.order_purchase_timestamp).dt.total_seconds() / 86400
    fact.loc[~delivered | fact.delivery_days.lt(0), "delivery_days"] = float("nan")
    fact["delay_days"] = (fact.order_delivered_customer_date.dt.normalize() - fact.order_estimated_delivery_date.dt.normalize()).dt.days.clip(lower=0)
    fact.loc[~fact.delivery_eligible, "delay_days"] = float("nan")
    fact["is_delivered"] = delivered
    fact["is_cancelled"] = fact.order_status.eq("canceled")
    item_fact = items.merge(silver["products"][["product_id", "product_category_name"]], on="product_id", validate="many_to_one")
    item_fact = item_fact.merge(silver["translation"], on="product_category_name", how="left", validate="many_to_one")
    item_fact["category"] = item_fact.product_category_name_english.fillna(item_fact.product_category_name).fillna("Unknown")
    item_fact = item_fact.merge(fact[["order_id", "purchase_date", "customer_state", "order_status", "delivery_eligible", "is_late", "delivery_days", "delay_days", "review_score"]], on="order_id", validate="many_to_one")
    assert_grain(item_fact, ["order_id", "order_item_id"])
    if len(item_fact) != len(items):
        raise ValueError("Item fact row-count mismatch")
    return {"fact_orders": fact, "fact_order_items": item_fact,
            "dim_geography": silver["geolocation"], "dim_customer": silver["customers"],
            "dim_product": silver["products"], "dim_seller": silver["sellers"]}
