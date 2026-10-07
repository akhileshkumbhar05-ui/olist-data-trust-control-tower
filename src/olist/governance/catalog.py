import pandas as pd
from olist.ingestion.catalog import SOURCES


def table_catalog():
    rows = []
    for layer in ("bronze", "silver"):
        for name, source in SOURCES.items():
            rows.append({"layer": layer, "table": name, "description": source.grain,
                         "grain": "One ZIP prefix" if layer == "silver" and name == "geolocation" else source.grain,
                         "key": ", ".join(source.key) or ("geolocation_zip_code_prefix" if layer == "silver" else "source_record_id"),
                         "owner": "Operations Data Product Owner", "source": "Kaggle Olist historical",
                         "classification": "Restricted customer/location data" if name in {"customers", "reviews", "geolocation"} else "Internal analytics",
                         "update_frequency": "Simulated purchase-date batches", "retention": "POC snapshot; production retention requires approval"})
    for table, grain in {"fact_orders": "One accepted order", "fact_order_items": "One accepted order/item", "dim_geography": "One canonical ZIP prefix", "dim_customer": "One order-specific customer ID", "dim_product": "One product", "dim_seller": "One seller"}.items():
        rows.append({"layer": "gold", "table": table, "description": grain,
                     "grain": grain, "key": {"fact_orders": "order_id", "fact_order_items": "order_id, order_item_id"}.get(table, "See data dictionary"),
                     "owner": "Operations Analytics Owner", "source": "Validated Silver",
                     "classification": "Internal analytics; identifiers restricted", "update_frequency": "After quality gate", "retention": "POC snapshot"})
    return pd.DataFrame(rows)


def lineage_catalog():
    rows = []
    for name, source in SOURCES.items():
        rows.extend([{"source": f"Kaggle:{source.filename}", "target": f"UC Volume/raw/{source.filename}", "kind": "ingestion"},
                     {"source": f"UC Volume/raw/{source.filename}", "target": f"bronze.{name}", "kind": "ingestion"},
                     {"source": f"bronze.{name}", "target": f"silver.{name}", "kind": "quality gate"}])
    for name in ("orders", "customers", "order_items", "payments", "reviews"):
        rows.append({"source": f"silver.{name}", "target": "gold.fact_orders", "kind": "aggregation/join"})
    for name in ("order_items", "products", "translation"):
        rows.append({"source": f"silver.{name}", "target": "gold.fact_order_items", "kind": "enrichment"})
    rows.extend([{"source": "gold.fact_orders", "target": "governed metrics", "kind": "central definitions"},
                 {"source": "governed metrics", "target": "Executive Overview", "kind": "presentation"}])
    return pd.DataFrame(rows)
