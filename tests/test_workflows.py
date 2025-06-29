import pytest
import yaml
import jsonschema
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
                    "id": {"type": "string"},
                    "event": {"type": "string", "enum": ["file_created", "message_received"]},
                    "path": {"type": "string"},
                    "queue": {"type": "string"},
                    "action_type": {"type": "string", "enum": ["script", "kubernetes"]},
                    "action": {"type": "string"},
                    "manifest": {"type": "string"},
                    "recursive": {"type": "boolean"},
                    "depends_on": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["event", "action_type"],
                "if": {"properties": {"event": {"const": "file_created"}}},
                "then": {"required": ["path"]},
                "else": {
                    "if": {"properties": {"event": {"const": "message_received"}}},
                    "then": {"required": ["queue"]}
                },
                "additionalProperties": False
            }
        }
    },
    "required": ["workflows"]
}


# test para cargar workflows validos
def test_cargar_workflows_valido(tmp_path):
    # contenido YAML de prueba
    yaml_content = """
    workflows:
      - id: process_file
        event: file_created
        path: /app/data
        action_type: script
        action: /app/scripts/process_data.sh <file>
        recursive: false
      - id: notify_message
        event: message_received
        queue: redis://redis:6379/0
        action_type: script
        action: python /app/src/notify.py
      - id: k8s_nginx
        event: file_created
        path: /app/data/k8s
        action_type: kubernetes
        manifest: /app/k8s/nginx-deployment.yaml
        depends_on: [process_file]
    """
    # crea archivo workflows.yaml de prueba
    archi = tmp_path / "workflows.yaml"
    archi.write_text(yaml_content)
    # carga y valida el YAML
    with open(archi) as f:
        workflows = yaml.safe_load(f)
    jsonschema.validate(instance=workflows, schema=schema)
    # verifica que se cargaron correctamente
    assert len(workflows["workflows"]) == 3
    assert workflows["workflows"][0]["recursive"] is False
    assert workflows["workflows"][2]["action_type"] == "kubernetes"
    assert workflows["workflows"][2]["manifest"] == "/app/k8s/nginx-deployment.yaml"


# test para cargar workflows invalidos
def test_cargar_workflows_invalido():
    # contenido YAML invalido
    invalid_yaml = """
    workflows:
      - event: invalid_event
        action_type: script
        action: echo test
    """
    # verifica que se lanza error de validacion
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=yaml.safe_load(invalid_yaml), schema=schema)


# test para init_state
@patch("os.path.exists", return_value=False)
@patch("builtins.open", new_callable=mock_open)
def test_init_state_crea_archivo(mock_open_func, mock_exists):
    # ejecuta funcion
    workflow_deps.init_state()
    # verifica que se creo el archivo
    mock_open_func.assert_called_once_with("/app/data/workflow_state.json", 'w')
    # verifica que se escribio JSON vacio
    handle = mock_open_func()
    handle.write.assert_called_once_with("{}")


# test para update_workflow_state
@patch("os.path.exists", return_value=True)
@patch("builtins.open", new_callable=mock_open, read_data='{}')
def test_update_workflow_state_agrega_estado(mock_open_func, mock_exists):
    # ejecuta funcion
    workflow_deps.update_workflow_state("workflow1", "success")
    # verifica que se abrio el archivo
    calls = mock_open_func.call_args_list
    assert calls[0][0][0] == "/app/data/workflow_state.json"
    # verifica que se escribio algo
    handle = mock_open_func()
    handle.write.assert_called()


# test para check_dependencies: sin dependencias
def test_check_dependencies_sin_dependencias():
    # ejecuta funcion sin dependencias
    resultado = workflow_deps.check_dependencies({"id": "1", "event": "x"})
    # verifica resultado
    assert resultado is True


# test para check_dependencies: con dependencias cumplidas
@patch("os.path.exists", return_value=True)
@patch("builtins.open", new_callable=mock_open, read_data='{"dep1": "success", "dep2": "success"}')
def test_check_dependencies_con_dependencias_ok(mock_open_func, mock_exists):
    # flujo con multiples dependencias
    workflow = {"depends_on": ["dep1", "dep2"]}
    # ejecuta funcion
    resultado = workflow_deps.check_dependencies(workflow)
    # verifica resultado
    assert resultado is True


# test para check_dependencies: con dependencias fallidas
@patch("os.path.exists", return_value=True)
@patch("builtins.open", new_callable=mock_open, read_data='{"dep1": "failed"}')
def test_check_dependencies_con_dependencias_fallidas(mock_open_func, mock_exists):
    # flujo con dependencia fallida
    workflow = {"depends_on": ["dep1"]}
    # ejecuta funcion
    resultado = workflow_deps.check_dependencies(workflow)
    # verifica resultado
    assert resultado is False


# test para check_dependencies: error al leer archivo
@patch("os.path.exists", return_value=True)
@patch("builtins.open", side_effect=Exception("Falla al leer"))
def test_check_dependencies_con_error(mock_open_func, mock_exists):
    # flujo con dependencia
    workflow = {"depends_on": ["dep1"]}
    # ejecuta funcion
    resultado = workflow_deps.check_dependencies(workflow)
    # verifica resultado
    assert resultado is False
