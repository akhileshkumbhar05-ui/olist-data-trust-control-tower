# Five-minute VP Operations demo — actual Olist findings

Validated locally using actual Kaggle Olist version 2, full accepted cohort, run `0c590b63fcbf4f3aa15ad994d80415f4`. Start the real-data app with `OLIST_DATA_ROOT=data streamlit run app/app.py`; verify its label is **REAL OLIST**, not DEMO / SYNTHETIC. Deployed Databricks validation is still pending. The dataset is historical, not live operations.

## 0:00–1:30 — Scenario 1: the metric and its trust evidence

Open Executive Overview. Say: “This product connects operational outcomes to the evidence behind them. We processed all nine historical Olist sources and published 99,433 accepted orders.”

Point to Delivered Item GMV, **BRL 13.22 million**, and **93.23% on-time delivery**. “GMV is delivered merchandise value, excluding freight; it is not accounting revenue. On-time compares calendar delivery dates to estimated dates.”

Point to **WARNING** and zero critical failures. “The data product exposes uncertainty alongside the KPI. A high opportunity-based score does not hide failed controls.” Open Metric Dictionary and select Total Orders or Delivered Item GMV: definition, owner, grain, formula and exclusions. Open Lineage / Trust: source CSV → governed raw landing design → Bronze → controls → Silver → Gold → metric → UI. Explain that this local demo displays declared paths; native UC lineage is verified after workspace execution.

## 1:30–3:15 — Scenario 2: a real quality incident and its retained records

Open Data Quality Command Center → Quality Incident Detail → **orders.delivered_time**. “Eight orders are labeled delivered but lack a customer-delivery event. We cannot use them as validated delivered facts.” Show HIGH severity, QUARANTINE action, source payload and actual processing run.

Open Quarantine Explorer; filter orders and that rule. “The original values remain inspectable. Bronze retains them, and Silver excludes them under a documented control.” Clear filters to show **32 distinct quarantined source records**: eight orders plus eight dependent items, eight payments and eight reviews. “Raw foreign keys existed, but a quarantined parent cannot silently leave trusted child facts.”

Show WARN controls for **1,373 lifecycle sequencing exceptions**, **303 payment-versus-item discrepancies**, and missing category/translation records. “These are investigation leads. Accounting/event semantics are not confirmed, so we disclose warnings rather than claim false root cause.”

Open Pipeline Health: **1,550,922 received = 1,550,890 accepted + 32 quarantined**, full historical cohort, successful publication. Explain that critical failures retain the previous snapshot; this rollback behavior is demonstrated by isolated automated tests, not invented source failures.

## 3:15–4:30 — Scenario 3: prioritize a real operations investigation

Open Operations Command Center. Keep full date range, customer state All, other filters All. Choose Customer state and minimum eligible deliveries 100. Compare **RJ: 1,495 late / 12,350 eligible (12.11%)** with **SP: 1,820 / 40,494 (4.49%)**.

Say: “SP has more late deliveries by count; RJ has a higher late rate. We can prioritize by exposure, rate and denominator rather than a misleading small-sample ranking.” Filter RJ and expand accepted order drilldown to show traceable order-level outcomes.

Optionally choose Seller with All filters: seller `4a3ca9315b744ce9f8e9374361493884` has **172 late deliveries / 1,772 eligible (9.71%)**. “This identifies a cohort to investigate; it does not prove seller fault. Multi-seller cohorts overlap.”

## 4:30–5:00 — Governance and the next deployment step

Open Data Governance and Pipeline Health. “We retain source checksums, versioned quality controls, original violations, explicit metric definitions and processing history. The app reads curated facts and quality outputs, never raw CSVs.”

End: “The real source, local medallion pipeline and all ten views are validated. The next step is authenticated execution in your Databricks workspace to verify UC objects, Serverless Job, SQL access, App permissions and captured native lineage. Catalog defaults to workspace; no classic cluster is required.”

## Demo safeguards

The figures belong to the documented run/definitions and may change if gates, filters or source versions change. Compare the UI's run ID with `docs/real_run_evidence.json` before presenting. Source files are historical; do not describe backlog as current/live. Distinguish declared local paths from executed native lineage. The separate `--demo` negative-price fixture remains clearly labeled DEMO / SYNTHETIC and must not be used to represent actual Olist incidents.
