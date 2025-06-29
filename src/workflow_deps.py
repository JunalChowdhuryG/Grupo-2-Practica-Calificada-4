import json
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/app/reports/workflow_deps.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

STATE_FILE = "/app/data/workflow_state.json"

def init_state():
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    if not os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'w') as f:
            json.dump({}, f)

def update_workflow_state(workflow_id, status):
    init_state()
    try:
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
        state[workflow_id] = status
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
        logger.info(f"Estado actualizado: {workflow_id} -> {status}")
    except Exception as e:
        logger.error(f"Error actualizando estado: {e}")
        raise

def check_dependencies(workflow):
    init_state()
    depends_on = workflow.get("depends_on", [])
    if not depends_on:
        return True
    try:
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
        for dep_id in depends_on:
            if state.get(dep_id) != "success":
                logger.warning(f"Dependencia {dep_id} no completada")
                return False
        return True
    except Exception as e:
        logger.error(f"Error verificando dependencias: {e}")
        return False