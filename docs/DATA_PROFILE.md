# Actual Olist source profile

Computed from every row of the immutable landed Kaggle files. ZIPs and IDs are read as strings; numeric/timestamp types below are inferred, not raw storage types.

## orders

File: `olist_orders_dataset.csv`. Rows: **99,441**; columns: 8; exact duplicates: 0.
Grain: One order. Candidate key: order_id. Rows in repeated candidate keys: 0.

| Field | Inferred type | Nulls | Null % | Distinct | Range / top values |
|---|---|---:|---:|---:|---|
| order_id | string | 0 | 0.0 | 99441 | High-cardinality identifier/text |
| customer_id | string | 0 | 0.0 | 99441 | High-cardinality identifier/text |
| order_status | string | 0 | 0.0 | 8 | {"delivered": 96478, "shipped": 1107, "canceled": 625, "unavailable": 609, "invoiced": 314} |
| order_purchase_timestamp | timestamp | 0 | 0.0 | 98875 | 2016-09-04 21:15:19 to 2018-10-17 17:30:18; parse failures 0 |
| order_approved_at | timestamp | 160 | 0.1609 | 90733 | 2016-09-15 12:16:38 to 2018-09-03 17:40:06; parse failures 0 |
| order_delivered_carrier_date | timestamp | 1783 | 1.793 | 81018 | 2016-10-08 10:34:01 to 2018-09-11 19:48:28; parse failures 0 |
| order_delivered_customer_date | timestamp | 2965 | 2.9817 | 95664 | 2016-10-11 13:46:32 to 2018-10-17 13:22:46; parse failures 0 |
| order_estimated_delivery_date | timestamp | 0 | 0.0 | 459 | 2016-09-30 00:00:00 to 2018-11-12 00:00:00; parse failures 0 |

## customers

File: `olist_customers_dataset.csv`. Rows: **99,441**; columns: 5; exact duplicates: 0.
Grain: One order-specific customer identity; customer_unique_id is persistent identity. Candidate key: customer_id. Rows in repeated candidate keys: 0.

| Field | Inferred type | Nulls | Null % | Distinct | Range / top values |
|---|---|---:|---:|---:|---|
| customer_id | string | 0 | 0.0 | 99441 | High-cardinality identifier/text |
| customer_unique_id | string | 0 | 0.0 | 96096 | High-cardinality identifier/text |
| customer_zip_code_prefix | string | 0 | 0.0 | 14994 | High-cardinality identifier/text |
| customer_city | string | 0 | 0.0 | 4119 | {"sao paulo": 15540, "rio de janeiro": 6882, "belo horizonte": 2773, "brasilia": 2131, "curitiba": 1521} |
| customer_state | string | 0 | 0.0 | 27 | {"SP": 41746, "RJ": 12852, "MG": 11635, "RS": 5466, "PR": 5045} |

## order_items

File: `olist_order_items_dataset.csv`. Rows: **112,650**; columns: 7; exact duplicates: 0.
Grain: One numbered item in an order. Candidate key: order_id, order_item_id. Rows in repeated candidate keys: 0.

| Field | Inferred type | Nulls | Null % | Distinct | Range / top values |
|---|---|---:|---:|---:|---|
| order_id | string | 0 | 0.0 | 98666 | High-cardinality identifier/text |
| order_item_id | number | 0 | 0.0 | 21 | 1.0 to 21.0; parse failures 0 |
| product_id | string | 0 | 0.0 | 32951 | High-cardinality identifier/text |
| seller_id | string | 0 | 0.0 | 3095 | High-cardinality identifier/text |
| shipping_limit_date | timestamp | 0 | 0.0 | 93318 | 2016-09-19 00:15:34 to 2020-04-09 22:35:08; parse failures 0 |
| price | number | 0 | 0.0 | 5968 | 0.85 to 6735.0; parse failures 0 |
| freight_value | number | 0 | 0.0 | 6999 | 0.0 to 409.68; parse failures 0 |

## payments

File: `olist_order_payments_dataset.csv`. Rows: **103,886**; columns: 5; exact duplicates: 0.
Grain: One payment sequence in an order. Candidate key: order_id, payment_sequential. Rows in repeated candidate keys: 0.

| Field | Inferred type | Nulls | Null % | Distinct | Range / top values |
|---|---|---:|---:|---:|---|
| order_id | string | 0 | 0.0 | 99440 | High-cardinality identifier/text |
| payment_sequential | number | 0 | 0.0 | 29 | 1.0 to 29.0; parse failures 0 |
| payment_type | string | 0 | 0.0 | 5 | {"credit_card": 76795, "boleto": 19784, "voucher": 5775, "debit_card": 1529, "not_defined": 3} |
| payment_installments | number | 0 | 0.0 | 24 | 0.0 to 24.0; parse failures 0 |
| payment_value | number | 0 | 0.0 | 29077 | 0.0 to 13664.08; parse failures 0 |

## reviews

File: `olist_order_reviews_dataset.csv`. Rows: **99,224**; columns: 7; exact duplicates: 0.
Grain: One review/order pair; review_id alone is not unique. Candidate key: review_id, order_id. Rows in repeated candidate keys: 0.

| Field | Inferred type | Nulls | Null % | Distinct | Range / top values |
|---|---|---:|---:|---:|---|
| review_id | string | 0 | 0.0 | 98410 | High-cardinality identifier/text |
| order_id | string | 0 | 0.0 | 98673 | High-cardinality identifier/text |
| review_score | number | 0 | 0.0 | 5 | 1.0 to 5.0; parse failures 0 |
| review_comment_title | string | 87656 | 88.3415 | 4527 | High-cardinality identifier/text |
| review_comment_message | string | 58247 | 58.7025 | 36159 | High-cardinality identifier/text |
| review_creation_date | timestamp | 0 | 0.0 | 636 | 2016-10-02 00:00:00 to 2018-08-31 00:00:00; parse failures 0 |
| review_answer_timestamp | timestamp | 0 | 0.0 | 98248 | 2016-10-07 18:32:28 to 2018-10-29 12:27:35; parse failures 0 |

## products

File: `olist_products_dataset.csv`. Rows: **32,951**; columns: 9; exact duplicates: 0.
Grain: One product. Candidate key: product_id. Rows in repeated candidate keys: 0.

| Field | Inferred type | Nulls | Null % | Distinct | Range / top values |
|---|---|---:|---:|---:|---|
| product_id | string | 0 | 0.0 | 32951 | High-cardinality identifier/text |
| product_category_name | string | 610 | 1.8512 | 73 | {"cama_mesa_banho": 3029, "esporte_lazer": 2867, "moveis_decoracao": 2657, "beleza_saude": 2444, "utilidades_domesticas": 2335} |
| product_name_lenght | number | 610 | 1.8512 | 66 | 5.0 to 76.0; parse failures 0 |
| product_description_lenght | number | 610 | 1.8512 | 2960 | 4.0 to 3992.0; parse failures 0 |
| product_photos_qty | number | 610 | 1.8512 | 19 | 1.0 to 20.0; parse failures 0 |
| product_weight_g | number | 2 | 0.0061 | 2204 | 0.0 to 40425.0; parse failures 0 |
| product_length_cm | number | 2 | 0.0061 | 99 | 7.0 to 105.0; parse failures 0 |
| product_height_cm | number | 2 | 0.0061 | 102 | 2.0 to 105.0; parse failures 0 |
| product_width_cm | number | 2 | 0.0061 | 95 | 6.0 to 118.0; parse failures 0 |

## sellers

File: `olist_sellers_dataset.csv`. Rows: **3,095**; columns: 4; exact duplicates: 0.
Grain: One seller. Candidate key: seller_id. Rows in repeated candidate keys: 0.

| Field | Inferred type | Nulls | Null % | Distinct | Range / top values |
|---|---|---:|---:|---:|---|
| seller_id | string | 0 | 0.0 | 3095 | High-cardinality identifier/text |
| seller_zip_code_prefix | string | 0 | 0.0 | 2246 | High-cardinality identifier/text |
| seller_city | string | 0 | 0.0 | 611 | {"sao paulo": 694, "curitiba": 127, "rio de janeiro": 96, "belo horizonte": 68, "ribeirao preto": 52} |
| seller_state | string | 0 | 0.0 | 23 | {"SP": 1849, "PR": 349, "MG": 244, "SC": 190, "RJ": 171} |

## geolocation

File: `olist_geolocation_dataset.csv`. Rows: **1,000,163**; columns: 5; exact duplicates: 261,831.
Grain: One observed ZIP/coordinate/city/state record; ZIP prefix is not unique. Candidate key: none; source row identity required. Rows in repeated candidate keys: None.

| Field | Inferred type | Nulls | Null % | Distinct | Range / top values |
|---|---|---:|---:|---:|---|
| geolocation_zip_code_prefix | string | 0 | 0.0 | 19015 | High-cardinality identifier/text |
| geolocation_lat | number | 0 | 0.0 | 717372 | -36.6053744107061 to 45.06593318269697; parse failures 0 |
| geolocation_lng | number | 0 | 0.0 | 717615 | -101.46676644931476 to 121.10539381057764; parse failures 0 |
| geolocation_city | string | 0 | 0.0 | 8011 | {"sao paulo": 135800, "rio de janeiro": 62151, "belo horizonte": 27805, "são paulo": 24918, "curitiba": 16593} |
| geolocation_state | string | 0 | 0.0 | 27 | {"SP": 404268, "MG": 126336, "RJ": 121169, "RS": 61851, "PR": 57859} |

## translation

File: `product_category_name_translation.csv`. Rows: **71**; columns: 2; exact duplicates: 0.
Grain: One category translation. Candidate key: product_category_name. Rows in repeated candidate keys: 0.

| Field | Inferred type | Nulls | Null % | Distinct | Range / top values |
|---|---|---:|---:|---:|---|
| product_category_name | string | 0 | 0.0 | 71 | {"beleza_saude": 1, "informatica_acessorios": 1, "automotivo": 1, "cama_mesa_banho": 1, "moveis_decoracao": 1} |
| product_category_name_english | string | 0 | 0.0 | 71 | {"health_beauty": 1, "computers_accessories": 1, "auto": 1, "bed_bath_table": 1, "furniture_decor": 1} |

## Relationships and join hazards

| Child → parent | Non-null child rows | Orphan rows | Max children / parent |
|---|---:|---:|---:|
| orders.customer_id → customers.customer_id | 99441 | 0 | 1 |
| order_items.order_id → orders.order_id | 112650 | 0 | 21 |
| order_items.product_id → products.product_id | 112650 | 0 | 527 |
| order_items.seller_id → sellers.seller_id | 112650 | 0 | 2033 |
| payments.order_id → orders.order_id | 103886 | 0 | 29 |
| reviews.order_id → orders.order_id | 99224 | 0 | 3 |
| products.product_category_name → translation.product_category_name | 32341 | 13 | 3029 |

- orders with multiple sellers: **1,278**
- orders with multiple payments: **2,961**
- orders with multiple reviews: **547**
- repeated review ids: **814**
- persistent customers with multiple order identities: **2,997**
- geolocation unique zip prefixes: **19,015**
- zip prefixes with multiple coordinates: **17,781**

Never join raw geolocation, items, payments or reviews together at order grain. Aggregate each child independently before joining; customer_id and customer_unique_id have different meanings.

Suspicious numeric/temporal/domain values are evaluated and persisted by the DQ framework; null review text is optional, and missing product category is a warning.
