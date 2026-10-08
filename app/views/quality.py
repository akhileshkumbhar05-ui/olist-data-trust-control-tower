import streamlit as st
import plotly.express as px


def command_center(service):
    st.subheader("Data Quality Command Center")
    results = service.latest_quality("dq_rule_results")
    score = service.latest_quality("dq_dataset_scorecard")
    cols = st.columns(4)
    cols[0].metric("Rules passed", int(results.status.eq("PASSED").sum()))
    cols[1].metric("Rules failed", int(results.status.eq("FAILED").sum()))
    cols[2].metric("Rule-record evaluations", int(results.records_evaluated.sum()))
    cols[3].metric("Rule-record failures", int(results.records_failed.sum()))
    st.caption("One source record may violate several rules; evaluation counts are not distinct source record counts.")
    st.dataframe(score, hide_index=True, width="stretch")
    failed = results[results.records_failed.gt(0)]
    if len(failed):
        st.plotly_chart(px.bar(failed.groupby(["severity", "rule_type"]).records_failed.sum().reset_index(), x="rule_type", y="records_failed", color="severity", title="Failures by rule category"), config={"responsive": True})
    history = service.quality_history()
    if len(history) > 1:
        st.plotly_chart(px.line(history, x="execution_timestamp", y="quality_score", title="Quality score across processing attempts"), config={"responsive": True})
    st.dataframe(results[["rule_id", "dataset", "rule_name", "rule_type", "severity", "action", "status", "records_evaluated", "records_failed", "failure_percentage", "run_id"]], hide_index=True, width="stretch")
    st.caption("Inspect a failure in Quality Incident Detail. Score = 100 × (1 − failed rule-record opportunities / evaluated opportunities); no hidden severity weights.")


def incident(service):
    st.subheader("Quality Incident Detail")
    results = service.latest_quality("dq_rule_results")
    failed = results[results.status.isin(["FAILED", "ERROR"])]
    if failed.empty:
        st.success("No failed rules in the latest quality run.")
        return
    selected = st.selectbox("Failed rule", failed.rule_id.tolist())
    rule = failed[failed.rule_id.eq(selected)].iloc[0]
    st.write(rule.rule_name)
    st.dataframe(rule.to_frame("Value"), width="stretch")
    failures = service.latest_quality("dq_failed_records")
    examples = failures[failures.rule_id.eq(selected)]
    st.markdown("**Confirmed impact**")
    st.write(f"{int(rule.records_failed):,} failed evaluations. Action: {rule.action}. This shows data-control failures; it does not establish an operational root cause.")
    st.markdown("**Potential downstream exposure**")
    st.code(f"bronze.{rule.dataset} → silver.{rule.dataset} → gold facts → governed operations metrics")
    st.write("Quarantine excludes affected source records; WARN retains them with disclosed uncertainty. Parent exclusions can also remove dependent children.")
    st.dataframe(examples.head(100), hide_index=True, width="stretch")


def quarantine(service):
    st.subheader("Quarantine Explorer")
    audits = service.audits()
    run_id = st.selectbox("Processing run", audits.run_id.tolist())
    try:
        frame = service.table("quarantine", run_id)
    except FileNotFoundError:
        st.info("This attempt failed before quarantine persistence; inspect Pipeline Health.")
        return
    if frame.empty:
        st.success("No quarantined source records in this run.")
        return
    cols = st.columns(3)
    for column, field in zip(cols, ["dataset", "rule_id", "severity"]):
        choice = column.selectbox(field.replace('_', ' ').title(), ["All"] + sorted(frame[field].unique().tolist()))
        if choice != "All":
            frame = frame[frame[field].eq(choice)]
    st.caption(f"{frame.source_record_id.nunique():,} distinct source records in selection; violations remain separate rows.")
    st.dataframe(frame, hide_index=True, width="stretch")
    st.download_button("Download selected violations", frame.to_csv(index=False), "quarantine_selection.csv", "text/csv")
