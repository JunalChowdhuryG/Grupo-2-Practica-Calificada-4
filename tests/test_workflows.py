import pytest
import yaml
import jsonschema
from jsonschema import validate

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
