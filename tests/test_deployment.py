from pathlib import Path
import yaml
from olist.quality.rules import RULES


def test_deployment_paths_and_resource_binding():
    bundle = yaml.safe_load(Path("databricks.yml").read_text())
    app = yaml.safe_load(Path("app.yaml").read_text())
    task = bundle["resources"]["jobs"]["olist_pipeline"]["tasks"][0]
    assert Path(task["spark_python_task"]["python_file"]).exists()
    assert Path(app["command"][2]).exists()
    warehouse = next(e for e in app["env"] if e["name"] == "DATABRICKS_SQL_WAREHOUSE_ID")
    resource = bundle["resources"]["apps"]["control_tower"]["resources"][0]
    assert warehouse["valueFrom"] == resource["name"]
    assert resource["sql_warehouse"]["permission"] == "CAN_USE"
    assert bundle["resources"]["jobs"]["olist_pipeline"]["max_concurrent_runs"] == 1


def test_versioned_rule_metadata_is_complete_and_unique():
    assert len({r.rule_id for r in RULES}) == len(RULES)
    assert {r.kind for r in RULES} >= {"schema", "required", "unique", "fk", "timestamp", "number", "domain", "range", "lifecycle", "reconciliation"}
    for rule in RULES:
        assert rule.action in {"WARN", "FAIL", "QUARANTINE"}
        assert rule.severity in {"CRITICAL", "HIGH", "MEDIUM", "LOW"}
        assert rule.record()["expected_condition"]


def test_serverless_job_requires_no_classic_cluster_and_declares_dependencies():
    bundle = yaml.safe_load(Path('databricks.yml').read_text())
    job = bundle['resources']['jobs']['olist_pipeline']
    task = job['tasks'][0]
    assert 'existing_cluster_id' not in task
    assert 'new_cluster' not in task
    assert 'libraries' not in task
    assert 'cluster_id' not in bundle['variables']
    assert bundle['variables']['catalog']['default'] == 'workspace'
    environment = next(e for e in job['environments'] if e['environment_key'] == task['environment_key'])
    declared = [line for line in Path('requirements-pipeline.txt').read_text().splitlines() if line and not line.startswith('#')]
    assert environment['spec']['dependencies'] == declared


def test_requested_databricks_environment_names_and_legacy_fallback(tmp_path, monkeypatch):
    from olist.config import Config
    from app.services.data import DataService
    from unittest.mock import Mock
    monkeypatch.delenv('DATABRICKS_CATALOG', raising=False)
    monkeypatch.delenv('OLIST_CATALOG', raising=False)
    assert Config.from_env().catalog == 'workspace'
    monkeypatch.setenv('OLIST_CATALOG', 'legacy')
    assert Config.from_env().catalog == 'legacy'
    monkeypatch.setenv('DATABRICKS_CATALOG', 'chosen')
    assert Config.from_env().catalog == 'chosen'
    monkeypatch.setenv('OLIST_BACKEND', 'databricks')
    monkeypatch.setenv('DATABRICKS_SQL_WAREHOUSE_ID', 'canonical')
    monkeypatch.setenv('DATABRICKS_WAREHOUSE_ID', 'legacy')
    service = DataService(Config(tmp_path), client=Mock())
    assert service.warehouse == 'canonical'


def test_deployment_environment_mapping_requires_no_cluster():
    from scripts.deploy import bundle_environment
    result = bundle_environment({'DATABRICKS_HOST': 'https://example.invalid', 'DATABRICKS_SQL_WAREHOUSE_ID': 'warehouse', 'DATABRICKS_CATALOG': 'workspace'})
    assert result['BUNDLE_VAR_workspace_host'] == 'https://example.invalid'
    assert result['BUNDLE_VAR_warehouse_id'] == 'warehouse'
    assert result['BUNDLE_VAR_catalog'] == 'workspace'
    assert 'BUNDLE_VAR_cluster_id' not in result
