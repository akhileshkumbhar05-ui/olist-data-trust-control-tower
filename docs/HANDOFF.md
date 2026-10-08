# Engineering handoff

Built and locally validated the actual-data Operations & Data Trust product. **Live Databricks deployment is outstanding** because workspace URL, SQL warehouse ID and authenticated access are not yet available. The known catalog is `workspace`; default Serverless Jobs/notebook paths do not need a cluster ID.

| Requested handoff item | Delivered / evidence |
|---|---|
| What was built | Ten-view interactive control tower, 88-rule DQ framework, retained quarantine/violations, medallion pipeline, governed metrics, operational audit, governance and native deployment assets |
| Architecture selection | Entire deployed path inside Databricks: KaggleHub → UC Volume → Spark/Delta layers and Quality → SQL warehouse → Databricks App; Parquet harness for isolated local validation |
| Repository structure | `src/olist` domain modules; `app/views/services/components`; `pipelines`; `scripts`; `sql`; `tests`; `docs`; manifests and declared pinned dependencies |
| Databricks resources required | Existing `workspace` catalog, Serverless Jobs or an existing Serverless notebook, SQL warehouse, enabled Databricks Apps; dedicated `olist_*` schemas/raw Volume/tables created by pipeline |
| Remote resources actually created | **None**; no authenticated workspace execution. Local raw files, profiles, curated snapshots and app validation are actual executed work |
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
| Deployment status | Serverless bundle passes official CLI JSON schema; environment names mapped; notebook path implemented; authenticated validate/deploy/run outstanding |
| Implemented, not live validated | UC Volume/Delta integration, serverless workspace task compatibility, native comments/lineage, App resource/OAuth injection, warehouse SQL queries and UC/app grants |
| Known limits | Historical cumulative purchase cohorts, no CDC/as-of claim; source time/accounting assumptions; bounded app queries, shared app principal, no remediation workflow; native lineage must be inspected |
| Productionization | Real source CDC, stable offsets, server-side aggregates, separate environments/identities, privacy enforcement, SLOs/alerting, incident resolution/replay, CI/CD and retention policies |
| Run/deploy commands | README local workflow; DEPLOYMENT maps requested variables, exact commands, UI locations and least-privilege resource requirements |
| Polished five-minute demo | DEMO_SCRIPT now uses three **actual** findings: traceable GMV/on-time KPI, missing-delivery quarantine, RJ/SP or seller investigation; synthetic fixtures are separate |

## Configuration and next authenticated step

`DATABRICKS_CATALOG=workspace` is known. `DATABRICKS_HOST` and `DATABRICKS_SQL_WAREHOUSE_ID` are pending nonsecret settings. `DATABRICKS_CLUSTER_ID` is optional and unused for serverless. `DATABRICKS_SERVERLESS_ENVIRONMENT_VERSION` selects a supported Jobs environment. Legacy config names remain compatible.

Find workspace URL in the browser's base HTTPS address; find warehouse ID under SQL → SQL Warehouses → selected warehouse → Connection details. Serverless notebooks have no classic cluster ID. DEPLOYMENT lists UI paths, Serverless Jobs checks and minimum deployment/pipeline/app permissions. Configure authentication in secure settings; never paste tokens/client secrets into chat or source code.

Continue local development without these identifiers. For native execution, the existing Serverless notebook entrypoint only needs repository/dependencies and UC permissions inside the workspace; it does not need an external token or warehouse. The deployed App still needs a SQL warehouse and its own read grants.

The actual data/profile/UI evidence is local, not a claim that remote UC objects or captured lineage already exist. After authenticated execution, inspect audit, facts, quarantine, App pages, permissions and native lineage before calling the Databricks POC deployed.
