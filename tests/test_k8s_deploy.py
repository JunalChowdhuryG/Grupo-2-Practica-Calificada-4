import pytest
from unittest.mock import patch, MagicMock, mock_open
import yaml
from kubernetes.client.rest import ApiException
from src import k8s_deploy

# contenido YAML basado en nginx-deployment.yaml
NGINX_YAML = """
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
  namespace: default
spec:
  replicas: 1
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:1.14.2
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: nginx-service
  namespace: default
spec:
  selector:
    app: nginx
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP
"""


# test  load_manifest
def test_carga_manifest_correctamente():
    # simula archivo abierto con contenido de nginx-deployment.yaml
    with patch("builtins.open", mock_open(read_data=NGINX_YAML)):
        resultado = k8s_deploy.load_manifest("k8s/nginx-deployment.yaml")
        # verifica que se cargaron dos documentos
        assert len(resultado) == 2
        # verifica Deployment
        assert resultado[0]["kind"] == "Deployment"
        assert resultado[0]["metadata"]["name"] == "nginx-deployment"
        assert resultado[0]["spec"]["replicas"] == 1
        assert resultado[0]["spec"]["selector"]["matchLabels"]["app"] == "nginx"
        # verifica Service
        assert resultado[1]["kind"] == "Service"
        assert resultado[1]["metadata"]["name"] == "nginx-service"
        assert resultado[1]["spec"]["ports"][0]["port"] == 80
        assert resultado[1]["spec"]["type"] == "ClusterIP"


# test  error al cargar manifiesto no encontrado
def test_error_manifest_no_encontrado():
    # simula error de archivo no encontrado
    with patch("builtins.open", side_effect=FileNotFoundError):
        with pytest.raises(FileNotFoundError):
            k8s_deploy.load_manifest("inexistente.yaml")


# test  error al cargar YAML invalido
def test_error_yaml_invalido():
    # contenido YAML invalido
    contenido_invalido = "key: : value: otro"
    # simula archivo abierto con contenido invalido
    with patch("builtins.open", mock_open(read_data=contenido_invalido)):
        with pytest.raises(yaml.YAMLError):
            k8s_deploy.load_manifest("manifesto_invalido.yaml")


# test  aplicar manifiesto de tipo Deployment
@patch("kubernetes.client.AppsV1Api")
@patch("kubernetes.client.CoreV1Api")
@patch("kubernetes.config.load_kube_config")
def test_aplica_manifest_deployment(mock_config, mock_core_api, mock_apps_api):
    # manifiesto de prueba basado en nginx-deployment.yaml
    manifest = {
        "kind": "Deployment",
        "metadata": {"name": "nginx-deployment", "namespace": "default"},
        "spec": {"replicas": 1, "selector": {"matchLabels": {"app": "nginx"}}}
    }
    # configura mock  API
    mock_api = MagicMock()
    mock_apps_api.return_value = mock_api
    # simula que el despliegue no existe (404)
    mock_api.read_namespaced_deployment.side_effect = ApiException(status=404)
    # ejecuta funcion
    resultado = k8s_deploy.apply_manifest(manifest)
    # verifica resultado
    assert resultado is True
    # verifica que se llamo a create_namespaced_deployment
    mock_api.create_namespaced_deployment.assert_called_once_with("default", manifest)
    # verifica que no se llamo a replace
    mock_api.replace_namespaced_deployment.assert_not_called()


# test  aplicar manifiesto de tipo Service
@patch("kubernetes.client.AppsV1Api")
@patch("kubernetes.client.CoreV1Api")
@patch("kubernetes.config.load_kube_config")
def test_aplica_manifest_service(mock_config, mock_core_api, mock_apps_api):
    # manifiesto de prueba basado en nginx-deployment.yaml
    manifest = {
        "kind": "Service",
        "metadata": {"name": "nginx-service", "namespace": "default"},
        "spec": {"ports": [{"port": 80, "targetPort": 80}], "type": "ClusterIP"}
    }
    # configura mock  API
    mock_api = MagicMock()
    mock_core_api.return_value = mock_api
    # simula que el servicio no existe (404)
    mock_api.read_namespaced_service.side_effect = ApiException(status=404)
    # ejecuta funcion
    resultado = k8s_deploy.apply_manifest(manifest)
    # verifica resultado
    assert resultado is True
    # verifica que se llamo a create_namespaced_service
    mock_api.create_namespaced_service.assert_called_once_with("default", manifest)
    # verifica que no se llamo a replace
    mock_api.replace_namespaced_service.assert_not_called()


# test  aplicar manifiesto de tipo Deployment existente
@patch("kubernetes.client.AppsV1Api")
@patch("kubernetes.client.CoreV1Api")
@patch("kubernetes.config.load_kube_config")
def test_aplica_manifest_deployment_existente(mock_config, mock_core_api, mock_apps_api):
    # manifiesto de prueba
    manifest = {
        "kind": "Deployment",
        "metadata": {"name": "nginx-deployment", "namespace": "default"}
    }
    # configura mock  API
    mock_api = MagicMock()
    mock_apps_api.return_value = mock_api
    # simula que el despliegue ya existe
    mock_api.read_namespaced_deployment.return_value = manifest
    # ejecuta funcion
    resultado = k8s_deploy.apply_manifest(manifest)
    # verifica resultado
    assert resultado is True
    # verifica que se llamo a replace_namespaced_deployment
    mock_api.replace_namespaced_deployment.assert_called_once_with("nginx-deployment", "default", manifest)
    # verifica que no se llamo a create
    mock_api.create_namespaced_deployment.assert_not_called()


# test  error al aplicar manifiesto
@patch("kubernetes.client.AppsV1Api")
@patch("kubernetes.client.CoreV1Api")
@patch("kubernetes.config.load_kube_config")
def test_error_api_al_aplicar_manifest(mock_config, mock_core_api, mock_apps_api):
    # manifiesto de prueba
    manifest = {"kind": "Deployment", "metadata": {"name": "nginx-deployment", "namespace": "default"}}
    # configura mock  error en API
    mock_api = MagicMock()
    mock_api.read_namespaced_deployment.side_effect = ApiException(status=500, reason="Server error")
    mock_apps_api.return_value = mock_api
    # ejecuta funcion
    resultado = k8s_deploy.apply_manifest(manifest)
    # verifica resultado
    assert resultado is False


# test  verificar despliegue listo
@patch("kubernetes.client.AppsV1Api")
@patch("kubernetes.config.load_kube_config")
def test_deployment_listo(mock_config, mock_apps_api):
    # configura mock  despliegue listo
    mock_deploy = MagicMock()
    mock_deploy.status.ready_replicas = 1
    mock_deploy.spec.replicas = 1
    mock_api = MagicMock()
    mock_api.read_namespaced_deployment.return_value = mock_deploy
    mock_apps_api.return_value = mock_api
    # ejecuta funcion
    resultado = k8s_deploy.check_deployment_status("nginx-deployment")
    # verifica resultado
    assert resultado is True


# test  verificar despliegue no listo
@patch("kubernetes.client.AppsV1Api")
@patch("kubernetes.config.load_kube_config")
def test_deployment_no_listo(mock_config, mock_apps_api):
    # configura mock  despliegue no listo
    mock_deploy = MagicMock()
    mock_deploy.status.ready_replicas = 0
    mock_deploy.spec.replicas = 1
    mock_api = MagicMock()
    mock_api.read_namespaced_deployment.return_value = mock_deploy
    mock_apps_api.return_value = mock_api
    # ejecuta funcion con un solo intento
    resultado = k8s_deploy.check_deployment_status("nginx-deployment", retries=1, delay=0)
    # verifica resultado
    assert resultado is False


# test  verificar reintentos en despliegue
@patch("kubernetes.client.AppsV1Api")
@patch("kubernetes.config.load_kube_config")
def test_deployment_retry_exitoso(mock_config, mock_apps_api):
    # configura mock  despliegue inicialmente no listo, luego listo
    mock_deploy_no_listo = MagicMock()
    mock_deploy_no_listo.status.ready_replicas = 0
    mock_deploy_no_listo.spec.replicas = 1
    mock_deploy_listo = MagicMock()
    mock_deploy_listo.status.ready_replicas = 1
    mock_deploy_listo.spec.replicas = 1
    mock_api = MagicMock()
    mock_api.read_namespaced_deployment.side_effect = [mock_deploy_no_listo, mock_deploy_listo]
    mock_apps_api.return_value = mock_api
    # ejecuta funcion con dos intentos
    resultado = k8s_deploy.check_deployment_status("nginx-deployment", retries=2, delay=0)
    # verifica resultado
    assert resultado is True
    # verifica que se llamo dos veces a read_namespaced_deployment
    assert mock_api.read_namespaced_deployment.call_count == 2


# test  error al leer despliegue
@patch("kubernetes.client.AppsV1Api")
@patch("kubernetes.config.load_kube_config")
def test_error_leyendo_deployment(mock_config, mock_apps_api):
    # configura mock  error en API
    mock_api = MagicMock()
    mock_api.read_namespaced_deployment.side_effect = ApiException(status=500, reason="Server error")
    mock_apps_api.return_value = mock_api
    # ejecuta funcion
    resultado = k8s_deploy.check_deployment_status("nginx-deployment")
    # verifica resultado
    assert resultado is False


# test  flujo completo deploy
@patch("src.k8s_deploy.check_deployment_status", return_value=True)
@patch("src.k8s_deploy.apply_manifest", return_value=True)
@patch("src.k8s_deploy.load_manifest", return_value=yaml.safe_load_all(NGINX_YAML))
def test_deploy_exitoso_multi_documento(mock_load, mock_apply, mock_check):
    # ejecuta funcion deploy
    resultado = k8s_deploy.deploy("k8s/nginx-deployment.yaml")
    # verifica resultado
    assert resultado is True
    # verifica que apply_manifest se llamo dos veces para Deployment y Service
    assert mock_apply.call_count == 2
