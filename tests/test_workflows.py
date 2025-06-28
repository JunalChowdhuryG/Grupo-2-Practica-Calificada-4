import pytest
import yaml
import jsonschema
from jsonschema import validate
from unittest.mock import patch, mock_open
from src import workflow_deps

# Definimos el esquema afuera para poder reutilizarlo en los tests
schema = {
    "type": "object",
    "properties": {
        "workflows": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "event": {"type": "string", "enum": ["file_created", "message_received", "k8s_deploy"]},
                    "path": {"type": "string"},
                    "queue": {"type": "string"},
                    "manifest": {"type": "string"},
                    "action": {"type": "string"},
                },
                "required": ["event", "action"],
                "if": {"properties": {"event": {"const": "file_created"}}},
                "then": {"required": ["path"]},
                "else": {
                    "if": {"properties": {"event": {"const": "message_received"}}},
                    "then": {"required": ["queue"]}
                }
            }
        }
    },
    "required": ["workflows"]
}


def test_cargar_workflows_valido():
    with open("/app/docs/workflows.yaml") as f:
        workflows = yaml.safe_load(f)

    validate(instance=workflows, schema=schema)
    assert len(workflows["workflows"]) == 3
    assert workflows["workflows"][2]["event"] == "k8s_deploy"
    assert "<manifest>" in workflows["workflows"][2]["action"]
    assert "manifest" in workflows["workflows"][2]


def test_cargar_workflows_invalido():
    invalid_yaml = """
    workflows:
      - event: invalid_event
        action: echo test
    """
    with pytest.raises(jsonschema.ValidationError):
        validate(instance=yaml.safe_load(invalid_yaml), schema=schema)


# test para init_state
@patch("os.path.exists", return_value=False)
@patch("builtins.open", new_callable=mock_open)
def test_init_state_crea_archivo(mock_open_func, mock_exists):
    workflow_deps.init_state()
    mock_open_func.assert_called_once_with("/app/data/workflow_state.json", 'w')
    handle = mock_open_func()
    handle.write.assert_called_once_with("{}")  # Se escribe un JSON vacío


# test para update_workflow_state
@patch("os.path.exists", return_value=True)
@patch("builtins.open", new_callable=mock_open, read_data='{}')
def test_update_workflow_state_agrega_estado(mock_open_func, mock_exists):
    workflow_deps.update_workflow_state("workflow1", "success")
    calls = mock_open_func.call_args_list
    assert calls[0][0][0] == "/app/data/workflow_state.json"
    handle = mock_open_func()
    handle.write.assert_called()  # Confirmamos que se escribió algo


# test para check_dependencies: sin dependencias
def test_check_dependencies_sin_dependencias():
    resultado = workflow_deps.check_dependencies({"id": "1", "event": "x"})
    assert resultado is True


# test para check_dependencies: con dependencias cumplidas
@patch("os.path.exists", return_value=True)
@patch("builtins.open", new_callable=mock_open, read_data='{"dep1": "success"}')
def test_check_dependencies_con_dependencias_ok(mock_open_func, mock_exists):
    workflow = {"depends_on": ["dep1"]}
    assert workflow_deps.check_dependencies(workflow) is True


# test para check_dependencies: con dependencias fallidas
@patch("os.path.exists", return_value=True)
@patch("builtins.open", new_callable=mock_open, read_data='{"dep1": "failed"}')
def test_check_dependencies_con_dependencias_fallidas(mock_open_func, mock_exists):
    workflow = {"depends_on": ["dep1"]}
    assert workflow_deps.check_dependencies(workflow) is False


# test para check_dependencies: error al leer archivo
@patch("os.path.exists", return_value=True)
@patch("builtins.open", side_effect=Exception("Falla al leer"))
def test_check_dependencies_con_error(mock_open_func, mock_exists):
    workflow = {"depends_on": ["dep1"]}
    assert workflow_deps.check_dependencies(workflow) is False
