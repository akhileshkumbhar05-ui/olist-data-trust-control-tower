import streamlit as st
import plotly.express as px
from app.components.common import display_value
from olist.metrics.definitions import METRICS


def render(service):
    st.subheader("Operations at a glance")
    values = service.metrics()
    keys = ["total_orders", "gmv", "on_time_rate", "review_score"]
    columns = st.columns(4)
    for column, key in zip(columns, keys):
        definition = next(m for m in METRICS if m.metric_id == key)
        column.metric(definition.name, display_value(values[key], definition.unit), help=definition.definition + ". " + definition.exclusions)
    st.caption("Purchase-cohort metrics from the published accepted facts. GMV excludes freight and is not accounting revenue.")
    summary = service.latest_quality("dq_run_summary").iloc[0]
    cols = st.columns(3)
    cols[0].metric("Quarantined source records", int(summary.quarantined_records))
    cols[1].metric("Critical rule failures", int(summary.critical_failures))
    cols[2].metric("Failed rules", int(summary.failed_rules))
    audits = service.audits()
    successful = audits[audits.status.eq("SUCCEEDED")]
    st.caption("Latest successful processing: " + (str(successful.iloc[0].ended_at) if len(successful) else "none"))
    left, right = st.columns([3, 2])
    fact, _ = service.filtered_facts()
    trend = fact.groupby("purchase_date").size().reset_index(name="orders")
    with left:
        st.plotly_chart(px.line(trend, x="purchase_date", y="orders", title="Accepted order volume by purchase date", color_discrete_sequence=["#147d92"]), config={"responsive": True})
    with right:
        st.markdown("**Investigation priorities**")
        ranking = service.rankings("seller_id")
        st.dataframe(ranking.head(5), hide_index=True, width="stretch")
        st.caption("Ranked by affected late-order count. Multi-seller orders may appear in each seller's cohort; late delivery does not establish seller fault.")
    with st.expander("Trace this KPI: Total Orders"):
        st.write("Count of accepted order IDs after quality and parent gates. One row per order; child tables are aggregated independently.")
        st.code("Kaggle orders → UC raw Volume → Bronze orders → DQ gates → Silver orders → Gold fact_orders → Total Orders → Executive Overview")
        st.write("Owner: Operations Analytics Owner. Open Metric Dictionary or Lineage / Trust for definitions and source paths.")
