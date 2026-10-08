# Executed validation

Validated in the Codex cloud machine on 2026-10-07, with additional live Databricks POC execution and UI smoke validation on 2026-10-08. Existing LICENSE is unchanged. Isolated tests/local validation remain separate from the live workspace run.

| Check | Result | Evidence / scope |
|---|---|---|
| Full pytest suite | **47 passed**, 0 failed, 27.79 seconds | Includes 3 native Spark tests, SQL client mocks, medallion/DQ/metric tests, all synthetic UI views, serverless/environment-binding regressions |
| Actual Kaggle acquisition | **Passed** | KaggleHub public version 2, TLS retained, original files copied to immutable raw landing and SHA-256 verified |
| All nine actual source profiles | **Passed** | Every source row scanned; actual schemas/null/distinct/range/duplicate/key/relationship/cardinality findings in DATA_PROFILE / data_profile.json |
| Full actual local medallion flow | **Passed** | Run `0c590b63fcbf4f3aa15ad994d80415f4`; 1,550,922 source records; 32 distinct quarantine; 99,433 Gold orders and 112,642 Gold items; WARNING disclosed |
| All ten actual-data app views | **Passed** | `scripts/validate_app.py` exercises existing curated real-data outputs via Streamlit AppTest; `artifacts/app_smoke.json` records every PASSED page |
| Native Spark/local parity | Passed on isolated fixture | Gold grains, complete metric set, geography and representative quality predicates; Spark 4.0.1 / Java 21; real full dataset run uses local harness |
| Critical gate / rollback behavior | Passed on fixture | Duplicate order key blocks new Gold; prior published snapshot retained |
| SQL data service | Passed with mocked SDK | Chunking, typed values, rejected truncation/failed statements, table/run-ID allowlist, environment aliases |
| Serverless bundle schema | Passed | Official checksum-verified CLI 0.270.0 schema; no cluster ID or cluster libraries in serverless task; dependencies supplied by environment key |
| Serverless notebook / native pipeline | **Passed live** | Existing Git-folder notebook executed successfully against the real Olist source. Live run `6cbe3a7f950346aea297f606274f3695` processed 1,550,922 source records, accepted 1,550,890, quarantined 32 and completed with WARNING / 0 critical failures |
| Python compilation/imports | Passed | `python -m compileall -q src app pipelines scripts` and executed workflow imports |
| Dependency compatibility / setup repeatability | Passed | `pip check`; tested `scripts/setup_cloud.sh`; official CLI checksum validation |
| Synthetic pipeline repeatability | Passed | Independent isolated run snapshots, 20 received = 19 accepted + 1 quarantine; not actual evidence |
| HTTP application startup | Passed | Local Streamlit health request `ok`; functional page checks provide behavior validation beyond a port |
| Live Unity Catalog / Delta assets | **Passed** | Live run created/used `olist_bronze`, `olist_silver`, `olist_gold` and `olist_quality`, the governed raw Volume, Delta snapshots, DQ history, audit and `published_run` pointer |
| Databricks App / SQL warehouse / app OAuth | **Passed** | App deployed from Git, attached to an existing SQL warehouse, and successfully queried governed Gold/Quality tables through its injected service principal; all ten views manually smoke-tested |
| App UC grants | **Passed for current POC** | App principal can USE CATALOG plus USE SCHEMA/SELECT on Gold and Quality; no Bronze/Silver/raw read access was granted |
| Native UC lineage inspection | **Pending** | The pipeline executed through named UC tables, but Catalog Explorer native table/column lineage coverage has not yet been manually recorded |
| Bundle-based Job/App deployment | **Not exercised live** | `databricks.yml` remains a validated IaC definition; the current live path used the Serverless notebook plus manual App-from-Git deployment |
| Three actual-source demo scenarios | Prepared from observed evidence | Traceable KPI, missing delivery-event incident/quarantine, RJ/SP or seller investigation; DEMO_SCRIPT |

Reproduce isolated tests with `pytest -q` after installing requirements-lock.txt. Actual data is ignored by Git and separate from `data/demo`. Reproduce source/profile with `KAGGLEHUB_CACHE=/workspace/kaggle-cache PYTHONPATH=src:. python scripts/acquire_profile.py`, full pipeline with `PYTHONPATH=src:. python scripts/run_local.py`, and actual page validation with `PYTHONPATH=src:. python scripts/validate_app.py`.

The original network-proxy blocker was resolved after environment configuration changed. A retry exposed and corrected the cache setting name: KaggleHub 0.3.13 uses `KAGGLEHUB_CACHE`, not `KAGGLEHUB_CACHE_DIR`. Acquisition now defaults to writable temporary staging if no cache path is supplied. Staging is not the governed raw landing.

Offline bundle compatibility and local Spark success remain separate evidence. The current Serverless notebook, Unity Catalog/Delta path, SQL-backed App and app-principal reads have now been exercised successfully as a POC. Bundle-based deployment, native lineage inspection and production-grade security/operational controls remain separate validation steps. Native code avoids classic caching/SparkContext APIs, uses SQL MERGE for audit updates, and pins UTC interpretation of source-naive timestamps; source timezone remains an explicit business assumption.
