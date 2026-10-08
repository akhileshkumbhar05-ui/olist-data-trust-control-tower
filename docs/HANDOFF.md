# Engineering handoff

Built, locally validated and **live-deployed as a Databricks POC**. The real Olist pipeline has executed through the existing Serverless notebook path, governed UC/Delta assets were created, and the SQL-backed Databricks App is running against those live outputs. The known catalog is `workspace`; the Serverless notebook path does not need a classic cluster ID.

| Requested handoff item | Delivered / evidence |
|---|---|
| What was built | Ten-view interactive control tower, 88-rule DQ framework, retained quarantine/violations, medallion pipeline, governed metrics, operational audit, governance and native deployment assets |
| Architecture selection | Entire deployed path inside Databricks: KaggleHub → UC Volume → Spark/Delta layers and Quality → SQL warehouse → Databricks App; Parquet harness for isolated local validation |
| Repository structure | `src/olist` domain modules; `app/views/services/components`; `pipelines`; `scripts`; `sql`; `tests`; `docs`; manifests and declared pinned dependencies |
| Databricks resources required | Existing `workspace` catalog, Serverless Jobs or an existing Serverless notebook, SQL warehouse, enabled Databricks Apps; dedicated `olist_*` schemas/raw Volume/tables created by pipeline |
| Live resources actually created/used | `olist_bronze`, `olist_silver`, `olist_gold`, `olist_quality`, governed raw Volume, Delta facts/dimensions and Quality/audit tables, `published_run`, an existing SQL warehouse resource, and the deployed Databricks App |
| Dataset profile summary | Nine sources fully scanned; 99,441 orders, 112,650 items, 103,886 payments, 99,224 reviews, 1,000,163 geolocation observations; full fields/counts in DATA_PROFILE |
| Confirmed grains | Unique orders/customer/product/seller IDs, order/item and order/payment-sequence pairs, review/order pair, source-category translation; geolocation remains observation grain |
| Confirmed cardinalities | 2,961 multi-payment, 547 multi-review, 1,278 multi-seller orders; 814 repeated review IDs; 17,781 ZIPs with multiple coordinates; child raw FKs have zero orphans except 13 product translations |
| Quality rules | Versioned schema/completeness/key/relationship/parse/domain/temporal/business controls; explicit FAIL/QUARANTINE/WARN and deterministic readiness |
| Actual DQ findings | Eight delivered orders lacking delivery timestamps; 1,373 lifecycle WARNs; 303 payment consistency WARNs; 610 missing categories; 13 missing translations. WARNING, zero critical failures |
| Actual operational findings | 99,433 accepted orders; BRL 13,220,248.93 delivered item GMV; 93.2269% on-time; 4.0864 latest review mean; RJ late rate 12.1053% versus SP 4.4945%; POC_FINDINGS contains populations/caveats |
| Governance capabilities | Machine-readable table/metric/declared-lineage catalogs, UC comments and logical owner/classification properties, access template and production policy recommendations; native enforcement/lineage unvalidated |
| Quarantine behavior | Eight invalid orders plus eight dependent items/payments/reviews each = 32 distinct source records; original payloads, each failure reason/rule/run retained; no silent exclusion |
| Pipeline observability | Received 1,550,922 = accepted source rows 1,550,890 + quarantine 32; starts/ends/status/duration/cohort/errors and snapshot publication; full local run 26.40 seconds |
| Business metrics | 13 centralized definitions/formulas: orders/delivered/canceled, delivered GMV/freight/AOV, on-time/late rates, delivery duration/delay, latest/negative reviews, persistent repeat-customer rate; segment rankings |
| App pages | Executive, Operations, DQ, Incident, Quarantine, Governance, Metric Dictionary, Lineage / Trust, Pipeline Health, Methodology; all ten exercised against actual curated outputs |
| Test results | **47 isolated tests passed**; 3 native Spark tests included; actual full source/profile/pipeline and ten actual UI page checks also passed; VALIDATION |
| Deployment status | Live Serverless notebook path and manual App-from-Git deployment passed. The App queries live Gold/Quality through an attached SQL warehouse. Bundle-based Job/App deployment remains unexercised |
| Remaining live validation | Native Catalog Explorer lineage inspection, bundle-based Job/App deployment, production user-specific authorization/masking, enterprise retention policy and production operational controls |
| Known limits | Historical cumulative purchase cohorts, no CDC/as-of claim; source time/accounting assumptions; bounded app queries, shared app principal, no remediation workflow; native lineage must be inspected |
| Productionization | Real source CDC, stable offsets, server-side aggregates, separate environments/identities, privacy enforcement, SLOs/alerting, incident resolution/replay, CI/CD and retention policies |
| Run/deploy commands | README local workflow; DEPLOYMENT maps requested variables, exact commands, UI locations and least-privilege resource requirements |
| Polished five-minute demo | DEMO_SCRIPT now uses three **actual** findings: traceable GMV/on-time KPI, missing-delivery quarantine, RJ/SP or seller investigation; synthetic fixtures are separate |

## Current configuration and remaining deployment work

`DATABRICKS_CATALOG=workspace` is the current catalog. The current workspace host and SQL warehouse are known to the deployed environment but intentionally not committed to source. `DATABRICKS_CLUSTER_ID` remains unused for the Serverless path. `DATABRICKS_SERVERLESS_ENVIRONMENT_VERSION` applies to the optional bundle Job path; the notebook environment is configured separately.

The current native execution path is validated: the existing Serverless notebook needs the repository, declared pipeline dependencies, UC permissions and Kaggle egress, but no external workspace token or SQL warehouse. The deployed App uses its attached SQL warehouse plus its generated service principal and Gold/Quality read grants.

The POC can now be called deployed. Remaining platform work is to inspect and document native lineage, optionally exercise the bundle-based Job/App deployment path, and move any production deployment into organization-managed identities, policies and environments.
