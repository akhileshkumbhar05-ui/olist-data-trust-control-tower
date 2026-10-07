import streamlit as st


def catalog(service):
    st.subheader("Governance catalog")
    st.dataframe(service.latest_quality("table_catalog"), hide_index=True, width="stretch")
    st.caption("Role-based owner labels are proposed governance responsibilities; live UC ownership and grants require workspace administration.")
    st.markdown("**Metric dictionary**")
    dictionary(service)


def dictionary(service):
    definitions = service.latest_quality("metric_dictionary")
    selected = st.selectbox("Metric definition", definitions.name.tolist())
    st.dataframe(definitions[definitions.name.eq(selected)].T.rename(columns=lambda _: "Definition"), width="stretch")


def lineage(service):
    st.subheader("Source-to-metric trust path")
    st.code("Kaggle orders CSV → UC raw Volume → Bronze orders\n    → Quality checks / Quarantine → Silver orders\n    → Gold fact_orders → Total Orders → Executive Overview")
    st.write("Column example: order_purchase_timestamp is preserved in Bronze, parsed in Silver, carried to Gold, and supplies purchase_date for the cohort filter and order trend. Total Orders counts distinct accepted order-grain rows.")
    st.dataframe(service.latest_quality("lineage_edges"), hide_index=True, width="stretch")
    st.caption("These are declared design paths. Open Catalog Explorer → the corresponding table → Lineage to inspect executed native UC lineage. Native column lineage is not claimed until verified in Databricks.")


def health(service):
    st.subheader("Pipeline Health")
    audits = service.audits()
    st.dataframe(audits, hide_index=True, width="stretch")
    st.caption("Received = accepted + distinct quarantined records before geolocation aggregation. Historical batches are cumulative purchase-date cutoffs, not live CDC. Geolocation canonical row reductions are intentional and separately documented.")


def methodology(service):
    st.subheader("How this product measures trust")
    st.write("Olist is a historical public dataset. Processing windows simulate incremental ingestion; they do not make the source live. Raw files are immutable and checksum-verified. Bronze preserves source values. Quality rules route violations to WARN, QUARANTINE, or FAIL. Silver standardizes accepted records, and Gold preserves order/item grain.")
    st.write("READY means all executed required gates passed. WARNING means noncritical quality exceptions exist. BLOCKED means a critical gate, FAIL action, missing check, or execution error prevents publication. Score alone never overrides a blocked state.")
    st.write("GMV is delivered merchandise value, not recognized revenue. Reviews use the latest answered review per order. Delivery lateness uses calendar dates. Seller ranking indicates exposure, not proof of seller fault.")
    st.write("Local mode is a Parquet development harness. The deployed application reads governed Gold and Quality Delta tables through a Databricks SQL warehouse using its injected service principal. No raw CSV reporting occurs in the app.")
    st.write("Current POC limits: bounded SQL result sets, no automated remediation, no incident acknowledgment workflow, no live source SLA, and workspace integration still requires authenticated validation.")
