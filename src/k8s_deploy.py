import logging
import yaml
from kubernetes import client, config
from kubernetes.client.exceptions import ApiException
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("reports/k8s_deploy.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_manifest(manifest_path):
    """Cargamos el manifiesto Kubernetes desde el archivo YAML."""
    try:
        with open(manifest_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error(f"Manifiesto {manifest_path} no encontrado")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Error parseando manifiesto {manifest_path}: {e}")
        raise

def apply_manifest(manifest):
    """Aplica un manifiesto Kubernetes al clúster."""
    try:
        config.load_kube_config()
        if os.environ.get("KUBERNETES_VERIFY_SSL", "true").lower() == "false":
            client.configuration.assert_hostname = False
            client.configuration.verify_ssl = False
        api = client.AppsV1Api()
        kind = manifest.get('kind', '').lower()
        metadata = manifest.get('metadata', {})
        namespace = metadata.get('namespace', 'default')
        name = metadata.get('name', '')

        if kind == 'deployment':
            api.create_namespaced_deployment(namespace, manifest)
            logger.info(f"Despliegue {name} creado en namespace {namespace}")
            return True
        else:
            logger.error(f"Tipo de manifiesto no soportado: {kind}")
            return False
    except ApiException as e:
        logger.error(f"Error aplicando manifiesto: {e}")
        return False

def check_deployment_status(deployment_name, namespace='default'):
    """Verificamos el estado del despliegue de Kubernetes.
    Args:
        deployment_name: Nombre del despliegue.
        namespace: Namespace del despliegue.
    Returns:
        bool: True si todos los pods están listos o False en caso contrario.
    """
    try:
        config.load_kube_config()
        api = client.AppsV1Api()
        deployment = api.read_namespaced_deployment(deployment_name, namespace)
        ready_replicas = deployment.status.ready_replicas or 0
        desired_replicas = deployment.spec.replicas
        if ready_replicas == desired_replicas:
            logger.info(f"Despliegue {deployment_name} listo: {ready_replicas}/{desired_replicas}")
            return True
        else:
            logger.warning(f"Despliegue {deployment_name} no listo: {ready_replicas}/{desired_replicas}")
            return False
    except ApiException as e:
        logger.error(f"Error verificando despliegue {deployment_name}: {e}")
        return False

def deploy(manifest_path):
    """Orquestamos el despliegue del manifiesto
    Args:
        manifest_path: Ruta al manifiesto YAML.
    Returns:
        bool: True si el despliegue fue exitoso o False en caso contrario.
    """
    manifest = load_manifest(manifest_path)
    if apply_manifest(manifest):
        metadata = manifest.get('metadata', {})
        deployment_name = metadata.get('name', '')
        namespace = metadata.get('namespace', 'default')
        return check_deployment_status(deployment_name, namespace)
    return False

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        logger.error("Uso: python k8s_deploy.py <manifest_path>")
        sys.exit(1)
    deploy(sys.argv[1])