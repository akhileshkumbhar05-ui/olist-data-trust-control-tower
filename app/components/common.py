import streamlit as st


def status_banner(summary, latest_audit):
    state = "BLOCKED" if latest_audit["status"] in {"BLOCKED", "FAILED", "RUNNING"} else summary["readiness"]
    text = f"Data product: {state} · {summary['data_label']}"
    if latest_audit["status"] in {"BLOCKED", "FAILED", "RUNNING"}:
        st.error(f"Latest attempt: {latest_audit['status']}. Metrics, if available, show the previous published run. {latest_audit['error_message']}")
    if state == "BLOCKED":
        st.error(text)
    elif state == "WARNING":
        st.warning(text + " · Review quality exceptions and metric coverage before decisions.")
    else:
        st.success(text)


def display_value(value, unit=""):
    if value is None or str(value) == "nan":
        return "N/A"
    if unit == "BRL":
        return f"R$ {value:,.2f}"
    if unit == "score":
        return f"{value:.2f}"
    if unit == "%":
        return f"{value:.1f}%"
    if unit == "days":
        return f"{value:.1f} days"
    return f"{value:,.0f}"
