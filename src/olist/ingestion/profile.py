"""Full-file profiling, including cardinality evidence; no sampled counts."""
from pathlib import Path
import json
import pandas as pd
from olist.ingestion.catalog import SOURCES, RELATIONSHIPS


def profile(tables: dict[str, pd.DataFrame], destination: Path) -> dict:
    result = {"datasets": {}, "relationships": []}
    lines = ["# Actual Olist source profile", "", "Computed from every row of the immutable landed Kaggle files. ZIPs and IDs are read as strings; numeric/timestamp types below are inferred, not raw storage types.", ""]
    for name, df in tables.items():
        spec = SOURCES[name]
        key_duplicates = int(df.duplicated(list(spec.key), keep=False).sum()) if spec.key else None
        info = {"filename": spec.filename, "rows": len(df), "columns": len(df.columns),
                "exact_duplicates": int(df.duplicated().sum()), "key": list(spec.key),
                "key_duplicate_rows": key_duplicates, "grain": spec.grain, "fields": {}}
        lines += [f"## {name}", "", f"File: `{spec.filename}`. Rows: **{len(df):,}**; columns: {len(df.columns)}; exact duplicates: {info['exact_duplicates']:,}.", f"Grain: {spec.grain}. Candidate key: {', '.join(spec.key) or 'none; source row identity required'}. Rows in repeated candidate keys: {key_duplicates}.", "", "| Field | Inferred type | Nulls | Null % | Distinct | Range / top values |", "|---|---|---:|---:|---:|---|"]
        for col in df:
            series = df[col]
            f = {"nulls": int(series.isna().sum()), "null_pct": round(100 * series.isna().mean(), 4), "distinct": int(series.nunique())}
            if col in spec.numeric:
                parsed = pd.to_numeric(series, errors="coerce")
                f.update(type="number", min=float(parsed.min()), max=float(parsed.max()), parse_failures=int((series.notna() & parsed.isna()).sum()))
                detail = f"{f['min']} to {f['max']}; parse failures {f['parse_failures']}"
            elif col in spec.timestamps:
                parsed = pd.to_datetime(series, errors="coerce", format="mixed")
                f.update(type="timestamp", min=str(parsed.min()), max=str(parsed.max()), parse_failures=int((series.notna() & parsed.isna()).sum()))
                detail = f"{f['min']} to {f['max']}; parse failures {f['parse_failures']}"
            else:
                f["type"] = "string"
                f["top_values"] = {str(k): int(v) for k, v in series.value_counts().head(5).items()}
                detail = json.dumps(f["top_values"], ensure_ascii=False) if f["distinct"] < 500 or col.endswith(("state", "city")) else "High-cardinality identifier/text"
            info["fields"][col] = f
            lines.append(f"| {col} | {f['type']} | {f['nulls']} | {f['null_pct']} | {f['distinct']} | {detail.replace('|', '/')} |")
        result["datasets"][name] = info
        lines.append("")
    lines += ["## Relationships and join hazards", "", "| Child → parent | Non-null child rows | Orphan rows | Max children / parent |", "|---|---:|---:|---:|"]
    for child, fk, parent, pk in RELATIONSHIPS:
        s = tables[child][fk]
        r = {"child": child, "fk": fk, "parent": parent, "pk": pk,
             "nonnull_child_rows": int(s.notna().sum()),
             "orphans": int((s.notna() & ~s.isin(tables[parent][pk])).sum()),
             "max_children_per_parent": int(s.value_counts().max())}
        result["relationships"].append(r)
        lines.append(f"| {child}.{fk} → {parent}.{pk} | {r['nonnull_child_rows']} | {r['orphans']} | {r['max_children_per_parent']} |")
    geo = tables["geolocation"]
    extras = {
        "orders_with_multiple_sellers": int((tables["order_items"].groupby("order_id").seller_id.nunique() > 1).sum()),
        "orders_with_multiple_payments": int((tables["payments"].groupby("order_id").size() > 1).sum()),
        "orders_with_multiple_reviews": int((tables["reviews"].groupby("order_id").size() > 1).sum()),
        "repeated_review_ids": int(tables["reviews"].review_id.duplicated().sum()),
        "persistent_customers_with_multiple_order_identities": int((tables["customers"].groupby("customer_unique_id").size() > 1).sum()),
        "geolocation_unique_zip_prefixes": int(geo.geolocation_zip_code_prefix.nunique()),
        "zip_prefixes_with_multiple_coordinates": int((geo.drop_duplicates(["geolocation_zip_code_prefix", "geolocation_lat", "geolocation_lng"]).groupby("geolocation_zip_code_prefix").size() > 1).sum()),
    }
    result["cardinality_findings"] = extras
    lines += ["", *[f"- {k.replace('_', ' ')}: **{v:,}**" for k, v in extras.items()], "", "Never join raw geolocation, items, payments or reviews together at order grain. Aggregate each child independently before joining; customer_id and customer_unique_id have different meanings.", "", "Suspicious numeric/temporal/domain values are evaluated and persisted by the DQ framework; null review text is optional, and missing product category is a warning."]
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "DATA_PROFILE.md").write_text("\n".join(lines) + "\n")
    (destination / "data_profile.json").write_text(json.dumps(result, indent=2))
    return result
