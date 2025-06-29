import logging
import yaml
import time
from kubernetes import client, config
from kubernetes.client.exceptions import ApiException

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app/reports/k8s_deploy.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_manifest(manifest_path):
    """Cargamos el manifiesto Kubernetes desde el archivo YAML."""
    try:
        with open(manifest_path, 'r') as f:
            return list(yaml.safe_load(f))
    except FileNotFoundError:
        logger.error(f"Manifiesto {manifest_path} no encontrado")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Error parseando manifiesto {manifest_path}: {e}")
        raise

def apply_manifest(manifest):
    """Aplica un manifiesto Kubernetes al clúster."""
    try:
        config.load_kube_config(config_file="/app/kubeconfig.yaml")
        api = client.AppsV1Api()
        core_api = client.CoreV1Api()
        kind = manifest.get('kind', '').lower()
        metadata = manifest.get('metadata', {})
        namespace = metadata.get('namespace', 'default')
        name = metadata.get('name', '')

        logger.info(f"Aplicando {kind}/{name} en namespace {namespace}")
        if kind == 'deployment':
            try:
                api.read_namespaced_deployment(name, namespace)
                api.replace_namespaced_deployment(name, namespace, manifest)
                logger.info(f"Despliegue {name} actualizado en namespace {namespace}")
            except ApiException as e:
                if e.status == 404:
                    api.create_namespaced_deployment(namespace, manifest)
                    logger.info(f"Despliegue {name} creado en namespace {namespace}")
                else:
                    logger.error(f"Error aplicando despliegue {name}: {e}")
                    raise
        elif kind == 'service':
            try:
                core_api.read_namespaced_service(name, namespace)
                core_api.replace_namespaced_service(name, namespace, manifest)
                logger.info(f"Servicio {name} actualizado en namespace {namespace}")
            except ApiException as e:
                if e.status == 404:
                    core_api.create_namespaced_service(namespace, manifest)
                    logger.info(f"Servicio {name} creado en namespace {namespace}")
                else:
                    logger.error(f"Error aplicando servicio {name}: {e}")
                    raise
        else:
            logger.error(f"Tipo de manifiesto no soportado: {kind}")
            return False
    except ApiException as e:
        logger.error(f"Error aplicando manifiesto: {e}")
        return False

def check_deployment_status(deployment_name, namespace='default', retries=10, delay=3):
    """ Verificamos el estado del despliegue de Kubernetes.
        True si todos los pods están listos o False en caso contrario.
    """
    try:
        config.load_kube_config(config_file="/app/kubeconfig.yaml")
        api = client.AppsV1Api()
        for attempt in range(retries):
            deployment = api.read_namespaced_deployment(deployment_name, namespace)
            ready_replicas = deployment.status.ready_replicas or 0
            desired_replicas = deployment.spec.replicas
            if ready_replicas == desired_replicas:
                logger.info(f"Despliegue {deployment_name} listo: {ready_replicas}/{desired_replicas}")
                return True
            else:
                logger.warning(f"Despliegue {deployment_name} no listo: {ready_replicas}/{desired_replicas} (intento {attempt + 1}/{retries})")
                time.sleep(delay)
        logger.error(f"Despliegue {deployment_name} no listo después de {retries} intentos")
        return False
    except Exception as e:
        logger.error(f"Error verificando despliegue {deployment_name}: {e}")
        return False

def deploy(manifest_path):
    """ Orquestamos el despliegue del manifiesto Kubernetes.
    """
    manifests = load_manifest(manifest_path)
    success = True
    deployment_name = None
    for manifest in manifests:
        if manifest.get('kind', '').lower() == 'deployment':
            deployment_name = manifest.get('metadata', {}).get('name', '')
        if not apply_manifest(manifest):
            success = False
    if success and deployment_name:
        return check_deployment_status(deployment_name)
    return False

if __name__ == "__main__": # pragma: no cover
    import sys
    if len(sys.argv) != 2:
        logger.error("Uso: python k8s_deploy.py <manifest_path>")
        sys.exit(1)
    deploy(sys.argv[1])