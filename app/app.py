import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]
import streamlit as st
from app.services.data import DataService
from app.components.common import status_banner
from app.pages import overview, operations, quality, governance

st.set_page_config(page_title="Olist · Operations & Data Trust", page_icon="◈", layout="wide")
st.markdown("""<style>.block-container{padding-top:2rem;max-width:1500px}h1{letter-spacing:-.035em}div[data-testid='stMetric']{background:#f1f5f9;border-radius:10px;padding:18px;color:#16324f}div[data-testid='stMetricLabel']{color:#47647b}</style>""", unsafe_allow_html=True)
st.title("E-Commerce Operations & Data Trust Control Tower")
st.caption("OLIST  /  HISTORICAL OPERATIONS  /  GOVERNED METRICS")

@st.cache_resource
def service():
    return DataService()

try:
    data = service()
    audits = data.audits()
    if audits.empty:
        st.info("No pipeline runs available. Run the ingestion and quality pipeline first.")
        st.stop()
    summary = data.latest_quality("dq_run_summary").iloc[0]
    status_banner(summary, audits.iloc[0])
except (FileNotFoundError, ValueError, RuntimeError, KeyError, IndexError) as exc:
    st.error(f"Data product unavailable: {exc}")
    st.info("Run the documented pipeline or configure the governed Databricks SQL connection. The app does not fall back to raw source files.")
    st.stop()

pages = {"Executive Overview": overview.render, "Operations Command Center": operations.render,
         "Data Quality Command Center": quality.command_center, "Quality Incident Detail": quality.incident,
         "Quarantine Explorer": quality.quarantine, "Data Governance": governance.catalog,
         "Metric Dictionary": governance.dictionary, "Lineage / Trust": governance.lineage,
         "Pipeline Health": governance.health, "About / Methodology": governance.methodology}
page = st.sidebar.radio("Explore", list(pages))
st.sidebar.caption(f"Data: {summary.data_label}\n\nQuality run: {summary.run_id[:12]}")
if st.sidebar.button("Refresh data"):
    st.cache_resource.clear()
    st.rerun()
try:
    pages[page](data)
except (FileNotFoundError, ValueError, RuntimeError, KeyError) as exc:
    st.error(f"This view is unavailable: {exc}")
    st.caption("Inspect Pipeline Health. A blocked or failed attempt never publishes replacement business facts.")
