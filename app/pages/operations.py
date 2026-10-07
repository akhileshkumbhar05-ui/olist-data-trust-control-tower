import streamlit as st
from olist.metrics.definitions import calculate, METRICS
from app.components.common import display_value


def render(service):
    st.subheader("Where should Operations investigate?")
    fact = service.table("fact_orders")
    items = service.table("fact_order_items")
    cols = st.columns(3)
    dates = cols[0].date_input("Purchase dates", value=(__import__('datetime').date.fromisoformat(fact.purchase_date.min()), __import__('datetime').date.fromisoformat(fact.purchase_date.max())))
    state = cols[1].selectbox("Customer state", ["All"] + sorted(fact.customer_state.dropna().unique().tolist()))
    status = cols[2].selectbox("Order status", ["All"] + sorted(fact.order_status.dropna().unique().tolist()))
    left, right = st.columns(2)
    seller = left.selectbox("Seller", ["All"] + sorted(items.seller_id.dropna().unique().tolist()))
    category = right.selectbox("Category", ["All"] + sorted(items.category.dropna().unique().tolist()))
    filters = {"state": None if state == "All" else state, "status": None if status == "All" else status,
               "seller": None if seller == "All" else seller, "category": None if category == "All" else category}
    if len(dates) == 2:
        filters.update(start=dates[0], end=dates[1])
    selected, _ = service.filtered_facts(**filters)
    if selected.empty:
        st.info("No accepted orders match this selection.")
        return
    values = calculate(selected)
    cols = st.columns(4)
    for c, key in zip(cols, ["total_orders", "late_rate", "delivery_days", "cancelled_orders"]):
        m = next(m for m in METRICS if m.metric_id == key)
        c.metric(m.name, display_value(values[key], m.unit), help=m.definition)
    st.caption("Seller/category filters select associated whole orders for order KPIs; segment GMV below includes only selected items. Segment rows are not additive across sellers/categories.")
    dimension = st.radio("Investigation view", ["Seller", "Category", "Customer state"], horizontal=True)
    key = {"Seller": "seller_id", "Category": "category", "Customer state": "customer_state"}[dimension]
    ranking = service.rankings(key, **filters)
    min_orders = st.number_input("Minimum eligible deliveries", min_value=0, value=1)
    if len(ranking):
        ranking = ranking[ranking.eligible_deliveries >= min_orders]
    st.dataframe(ranking.head(100), hide_index=True, width="stretch")
    st.caption("Ranked by late-order exposure, then cohort size. Source review and delivery outcomes support investigation; they do not prove causal responsibility.")
    with st.expander("Accepted order drilldown"):
        st.dataframe(selected.head(500), hide_index=True, width="stretch")
