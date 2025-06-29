import os
import time
import watchdog.events
from watchdog.observers.polling import PollingObserver
import yaml
import redis
import logging
import threading
import subprocess
from src.workflow_deps import check_dependencies, update_workflow_state
from src.workflow_deps import deploy


# Configura el sistema para escribir un log en un archivo y en la consola
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/app/reports/event_engine.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


# Manejo de eventos de archivos
class FileEventHandler(watchdog.events.FileSystemEventHandler):
    def __init__(self, workflows):
        self.workflows = workflows

    # Método que se llama cuando se crea un archivo
    def on_created(self, event):
        logger.debug(f"Evento detectado: {event}")
        if not event.is_directory:
            logger.info(f"Archivo creado: {event.src_path}")
            for wf in self.workflows:
                if wf["event"] == "file_created" :
                    esta_en_directorio = event.src_path.startswith(wf["path"])
                    es_recursivo = wf.get("recursive", True)
                    es_directorio_exacto = os.path.dirname(event.src_path) == wf["path"].rstrip("/")
                    if esta_en_directorio and (es_recursivo or es_directorio_exacto):
                        if check_dependencies(wf):
                            if wf.get("action_type") == "script":
                                action = wf["action"].replace("<file>", event.src_path)
                                logger.info(f"Ejecutando acción: {action}")
                                result = subprocess.run(action, shell=True, capture_output=True, text=True)
                                status = "success" if result.returncode == 0 else "failed"
                                update_workflow_state(wf.get("id",""), status)
                            elif wf.get("action_type") == "kubernetes":
                                logger.info(f"Ejecutando acción de Kubernetes: {wf['manifest']}")
                                succes = deploy(wf["manifest"])
                                status = "success" if succes else "failed"
                                update_workflow_state(wf.get("id", ""), status)
                        else:
                            logger.warning(f"Dependencias no cumplidas para workflow {wf.get('id', '')}")


# Carga la configuracion de workflows desde un YAML
def load_workflows(config_path):
    try:
        with open(config_path) as f:
            workflows = yaml.safe_load(f)["workflows"]
            for wf in workflows:
                wf["id"] = wf.get("id", f"workflow_{id(wf)}")
            return workflows
    except FileNotFoundError:
        logger.error(f"No se encontro {config_path}")
        exit(1)
    except yaml.YAMLError as e:
        logger.error(f"Error parseando {config_path}: {e}")
        exit(1)


# Manejo de la comunicacion con Redis
def listen_redis(queue, workflows):
    try:
        r = redis.Redis.from_url(queue, decode_responses=True)
        pubsub = r.pubsub()
        pubsub.subscribe("notifications")
        logger.info(f"Suscrito a Redis queue: {queue}")
        for message in pubsub.listen():
            if message["type"] == "message":
                logger.info(f"Mensaje recibido: {message['data']}")
                for wf in workflows:
                    if wf["event"] == "message_received" and wf["queue"] == queue:
                        logger.info(f"Ejecutando accion: {wf['action']}")
                        result = subprocess.run(wf["action"], shell=True, capture_output=True, text=True)
                        status = "success" if result.returncode == 0 else "failed"
                        update_workflow_state(wf.get("id", ""), status)
    except redis.RedisError as e:
        logger.error(f"Error de Redis: {e}")
        exit(1)


if __name__ == "__main__": # pragma: no cover
    data_dir = "/app/data"
    config_path = "/app/docs/workflows.yaml"
    redis_url = "redis://localhost:6379/0"

    if not os.path.exists(data_dir):
        logger.error(f"Directorio  {data_dir} no existe")
        exit(1)
    if not os.path.exists(config_path):
        logger.error(f"No se encontro {config_path} ")
        exit(1)

    workflows = load_workflows(config_path)

    # File observer
    observer = PollingObserver()
    for wf in workflows:
        if wf["event"] == "file_created":
            recursive = wf.get("recursive", True)
            observer.schedule(FileEventHandler(workflows), path=wf["path"], recursive=recursive)
    observer.start()
    time.sleep(2)
    logger.info(f"Monitoreando: {data_dir}")

    # Redis listener
    for wf in workflows:
        if wf["event"] == "message_received":
            redis_thread = threading.Thread(target=listen_redis, args=(wf["queue"], workflows))
            redis_thread.daemon = True
            redis_thread.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        logger.info("Apagando observer")
    observer.join()
