import os
import time
import watchdog.events
from watchdog.observers.polling import PollingObserver
import yaml
import redis
import logging
import threading

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
                if wf["event"] == "file_created" and event.src_path.startswith(
                    wf["path"]
                ):
                    action = wf["action"].replace("<file>", event.src_path)
                    logger.info(f"Ejecutando accion: {action}")
                    os.system(action)


# Carga la configuracion de workflows desde un YAML
def load_workflows(config_path):
    try:
        with open(config_path) as f:
            return yaml.safe_load(f)["workflows"]
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
                        os.system(wf["action"])
    except redis.RedisError as e:
        logger.error(f"Error de Redis: {e}")
        exit(1)


if __name__ == "__main__":
    data_dir = "/app/data"
    config_path = "/app/docs/workflows.yaml"
    if not os.path.exists(data_dir):
        logger.error(f"Directorio  {data_dir} no existe")
        exit(1)
    if not os.path.exists(config_path):
        logger.error(f"No se encontro {config_path} ")
        exit(1)
    workflows = load_workflows(config_path)
    # File observer
    observer = PollingObserver()
    observer.schedule(FileEventHandler(workflows), path=data_dir, recursive=False)
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
