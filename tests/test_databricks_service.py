"""Client boundary tests; no workspace calls or production writes."""
from types import SimpleNamespace as NS
from unittest.mock import Mock
import pytest
from databricks.sdk.service.sql import StatementState, ColumnInfoTypeName
from app.services.data import DataService
from olist.config import Config


def response(truncated=False, state=StatementState.SUCCEEDED):
    return NS(statement_id="test", status=NS(state=state), manifest=NS(truncated=truncated,
        schema=NS(columns=[NS(name="n", type_name=ColumnInfoTypeName.LONG), NS(name="eligible", type_name=ColumnInfoTypeName.BOOLEAN)])),
        result=NS(data_array=[["1", "true"]], next_chunk_index=1))


def service(monkeypatch):
    monkeypatch.setenv("OLIST_BACKEND", "databricks")
    monkeypatch.setenv("DATABRICKS_WAREHOUSE_ID", "test-warehouse")
    client = Mock()
    client.statement_execution.execute_statement.return_value = response()
    client.statement_execution.get_statement_result_chunk_n.return_value = NS(data_array=[["2", "false"]], next_chunk_index=None)
    return DataService(Config(), client), client


def test_sql_chunks_and_typed_conversion(monkeypatch):
    data, client = service(monkeypatch)
    result = data.query("SELECT 1")
    assert result.n.tolist() == [1, 2]
    assert result.eligible.tolist() == [True, False]
    assert client.statement_execution.get_statement_result_chunk_n.call_count == 1


def test_truncated_queries_fail_loudly(monkeypatch):
    data, client = service(monkeypatch)
    client.statement_execution.execute_statement.return_value = response(truncated=True)
    with pytest.raises(RuntimeError, match="truncated"):
        data.query("SELECT 1")


def test_unsuccessful_statement_is_not_shown_as_empty_success(monkeypatch):
    data, client = service(monkeypatch)
    client.statement_execution.execute_statement.return_value = response(state=StatementState.FAILED)
    with pytest.raises(RuntimeError, match="failed"):
        data.query("SELECT 1")


def test_only_known_tables_and_run_ids_are_accepted(monkeypatch):
    data, client = service(monkeypatch)
    with pytest.raises(ValueError):
        data.table("raw_orders")
    with pytest.raises(ValueError):
        data.table("quarantine", "x' OR 1=1")
    assert not client.statement_execution.execute_statement.called


def test_native_snapshot_pinning_predicate(monkeypatch):
    data, client = service(monkeypatch)
    data.table("fact_orders")
    sql = client.statement_execution.execute_statement.call_args.kwargs["statement"]
    assert "published_run" in sql
    assert "pipeline_run_id" in sql
    assert "SELECT *" not in sql
