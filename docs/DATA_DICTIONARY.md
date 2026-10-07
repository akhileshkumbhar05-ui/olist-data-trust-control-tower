# Data dictionary

Source fields and contracts are enumerated in `src/olist/ingestion/catalog.py`; candidate keys and relationship cardinalities were checked against every downloaded Olist row; see DATA_PROFILE. The profiler generates complete observed field types/ranges/null counts. Business descriptions below specify implemented semantics, business meaning beyond the observed profile still requires source-owner interpretation.

| Dataset / model | Grain within snapshot | Key / important fields |
|---|---|---|
| orders | One order | `order_id`; `customer_id` links an order-specific customer identity; final `order_status`; purchase/approval/carrier/customer-delivery/estimate timestamps |
| customers | One order-specific customer identity | `customer_id`; `customer_unique_id` is the persistent identity used for repeat-customer metrics; ZIP prefix retained as text |
| order_items | One numbered item per order | `(order_id, order_item_id)`; product/seller keys; price and freight in BRL; shipping deadline |
| payments | One payment sequence per order | `(order_id, payment_sequential)`; payment type, installments, payment value |
| reviews | One review/order pair | `(review_id, order_id)` validated unique in this snapshot; score and creation/answer dates; optional comment text; `review_id` alone is not assumed unique |
| products | One product | `product_id`; Portuguese category, dimensional/description fields |
| sellers | One seller | `seller_id`; city/state/ZIP |
| raw geolocation | One location observation | No assumed business key; repeated ZIP prefixes and coordinates remain preserved |
| translation | One source-category translation | `product_category_name`; English label |
| Silver geolocation | One ZIP prefix | Median latitude/longitude, modal city/state with lexicographic tie-breaker, `observation_count` |
| Gold fact_orders | One accepted order | Independently aggregated item/payment economics, latest review, customer persistent ID/state, operational flags |
| Gold fact_order_items | One accepted order/item | Product/category enrichment and associated order outcomes; order measures are not additive across item rows |
| dim_customer/product/seller/geography | One respective accepted entity / ZIP | POC dimensions preserve operational identities rather than slowly changing dimension history |

Bronze metadata: `source_record_id`, `source_file`, `pipeline_run_id`, `ingestion_timestamp`, `simulated_batch_id`, `simulated_batch_start`, `simulated_batch_end`. Spark row identities are unique **within a run**, not stable CSV byte offsets. Local identities use original CSV row ordinal. Always inspect with dataset and run ID.

Gold fields: `item_gmv` = accepted item prices per order; `freight_value` = accepted item freight; `payment_total` = accepted payment sum; `item_count`, `seller_count`, `payment_count`; `review_score` = latest accepted answered review; `purchase_date` = source purchase date; `is_delivered`, `is_cancelled`; `delivery_eligible` requires delivered status and delivery/estimate events; `is_late` compares calendar dates; `delivery_days` excludes negative elapsed intervals; `delay_days` is nonnegative date difference. Missing accepted child aggregates remain null, not fake zero-value orders.

Quality model: `dq_rules` contains versioned controls; `dq_rule_results` has each executed rule's count, percentage, action, status, samples and execution/run IDs; `dq_failed_records` retains WARN and rejected violations; `quarantine` contains QUARANTINE/FAIL records and accepted-parent exclusions; `dq_dataset_scorecard` shows accepted/quarantined counts and rule score; `dq_run_summary` exposes readiness; `pipeline_run_audit` shows lifecycle/counts/errors; `published_run` selects one successful business snapshot. A record violating several rules has several failure rows but one distinct quarantined record.

`table_catalog`, `metric_dictionary`, `lineage_edges` expose governance definitions through the app. Local snapshot files omit redundant history IDs where the directory encodes the run. Native tables are append-only across runs, so SQL must select a run.
