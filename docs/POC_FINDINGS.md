# Actual Olist findings and validation status

Kaggle public dataset `olistbr/brazilian-ecommerce`, downloaded version 2, profiled in full on 2026-10-07. Raw CSVs and SHA-256 manifest are retained under ignored `data/raw`; no source changes were made. Machine-readable full-file evidence is in `data_profile.json`; local curated-run evidence is in `real_run_evidence.json`.

The actual run ID is `0c590b63fcbf4f3aa15ad994d80415f4`. These findings are **actual historical source/local pipeline observations**, not synthetic fixtures or live Databricks results.

## Source grains and relationships

| Source | Rows | Observed key / interpretation |
|---|---:|---|
| orders | 99,441 | Unique order_id |
| customers | 99,441 | Unique customer_id; persistent customer_unique_id has repeat order identities |
| order_items | 112,650 | Unique order_id + order_item_id |
| payments | 103,886 | Unique order_id + payment_sequential |
| reviews | 99,224 | Unique review_id + order_id; review_id alone repeats 814 times |
| products | 32,951 | Unique product_id |
| sellers | 3,095 | Unique seller_id |
| geolocation | 1,000,163 | Observation grain, not ZIP grain; 261,831 exact duplicate observations; 19,015 distinct ZIP prefixes |
| translation | 71 | Unique Portuguese category key |

No raw FK orphans were found for order→customer, item→order/product/seller, payment→order, review→order. This does not mean accepted-parent integrity can be ignored: removing an invalid parent can invalidate otherwise valid child relationships.

There are 1,278 multi-seller orders, 2,961 multi-payment orders, 547 multi-review orders and 2,997 persistent customers with multiple order-specific customer identities. The maximum item/payment/review child counts per order are 21/29/3. There are 17,781 ZIP prefixes with multiple coordinates. These observed cardinalities justify separate child aggregation, one-review selection, distinct customer identities and canonical geography.

## Actual quality findings

| Rule | Failed records | Action / interpretation |
|---|---:|---|
| orders.delivered_time | 8 | HIGH / QUARANTINE: delivered status without customer-delivery timestamp |
| orders.lifecycle | 1,373 | MEDIUM / WARN: adjacent known delivered lifecycle events out of order; source event semantics need investigation |
| orders.payment_reconciliation | 303 | MEDIUM / WARN: payments versus item price + freight differ beyond BRL 0.01 when both are present; not proof of bad accounting |
| products.category | 610 | MEDIUM / WARN: missing category; retained with Unknown category fallback |
| products.fk_product_category_name | 13 | MEDIUM / WARN: 10 `portateis_cozinha_e_preparadores_de_alimentos` products and 3 `pc_gamer` products lack translation; Portuguese label retained |

All 88 controls executed. Five rules failed; no critical rule failed. The product is **WARNING**, with 99.9805% equally weighted rule-record opportunity score. A high score does not conceal the warnings.

Eight bad delivered orders are excluded from Silver; eight associated items, eight payment rows and eight reviews enter accepted-parent quarantine. Total distinct quarantined source records = **32** across four datasets. Every exclusion has a record/run/rule/reason and original payload. Received **1,550,922** = accepted source records **1,550,890** + quarantined **32**, before intentional geolocation aggregation. Silver geography canonicalizes accepted observations into **19,015 ZIP rows**.

The successful full local pipeline took 26.40 seconds. Gold has **99,433 order-grain rows** and **112,642 order/item-grain rows**, with explicit key/count checks. Raw source maximum purchase timestamp is historical 2018-10-17; this is event coverage, not live freshness.

## Actual operational findings from accepted Gold

| Metric | Observed value |
|---|---:|
| Total accepted orders | 99,433 |
| Delivered orders | 96,470 |
| Canceled orders | 625 |
| Delivered item GMV | BRL 13,220,248.93 |
| Delivered freight | BRL 2,198,145.90 |
| Average delivered order item value | BRL 137.04 |
| Date-level on-time delivery rate | 93.2269% |
| Date-level late delivery rate | 6.7731% |
| Mean purchase-to-delivery days | 12.5582 |
| Mean positive delay among late deliveries | 10.6201 calendar days |
| Latest accepted review mean | 4.0864 |
| Negative latest review rate (scores 1–2) | 14.6891% |
| Persistent repeat-customer rate, full accepted cohort | 3.1190% |

GMV is merchandise value on delivered orders, not accounting revenue. Freight is separate. Missing/negative delivery intervals are excluded according to the metric dictionary. On-time is a calendar-day comparison, not exact-midnight timestamp comparison. Review/latest policy and quarantine alter populations; totals are not raw-source totals.

For an actual operational investigation, customer state **RJ** has 12,350 eligible delivered orders and 1,495 late orders, a **12.1053%** late rate, compared with **SP**'s 40,494 eligible deliveries, 1,820 late orders and **4.4945%** late rate. Volume and rate answer different prioritization questions; neither proves causation. The highest late-order exposure seller is `4a3ca9315b744ce9f8e9374361493884`: 172 late deliveries among 1,772 eligible, 9.7065%. Multi-seller cohorts overlap, so seller totals are not additive.

## Synthetic validation remains separate

`tests/fixtures.py` supplies isolated DEMO / SYNTHETIC data, including an injected negative-price item for rejection tests. Those amounts and failures are never included in real findings. The clean fixture validates known GMV BRL 350; the deliberately invalid demo fixture yields BRL 300 after rejection. Duplicate-key fixtures verify blocked publication without altering actual data.

## Remaining live validation and limitations

No Databricks workspace URL/authentication/warehouse ID is available; no remote UC objects, Job, App, warehouse grants or native lineage were created/verified. The bundle defaults to configurable `workspace` catalog and Serverless Jobs; no cluster ID is needed. Native Spark logic is tested locally, while real full-file pipeline/UI validation uses the Parquet development harness.

The source is historical and cumulative simulation is not CDC or a point-in-time reconstruction. The app loads bounded curated results; larger/native results may need SQL aggregation/pagination. Payment/lifecycle semantics and source timezone are not business-owner-certified. Sensitivity properties are descriptive until administrators enforce grants/masking. Source row surrogates are run-local. Three actual-source demo scenarios are now documented, but live Databricks delivery still requires the deployment runbook.
