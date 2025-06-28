import pytest
from unittest.mock import patch, mock_open, MagicMock
from src import k8s_deploy
import yaml


# test para load_manifest
def test_carga_manifest_correctamente():
    contenido_yaml = "kind: Deployment\nmetadata:\n  name: mi-deploy\n"
    with patch("builtins.open", mock_open(read_data=contenido_yaml)):
        resultado = k8s_deploy.load_manifest("ruta/ficticia.yaml")
        assert resultado["kind"] == "Deployment"
        assert resultado["metadata"]["name"] == "mi-deploy"


def test_error_manifest_no_encontrado():
    with patch("builtins.open", side_effect=FileNotFoundError):
        with pytest.raises(FileNotFoundError):
            k8s_deploy.load_manifest("inexistente.yaml")


def test_error_yaml_invalido():
    contenido_invalido = "key: : value: otro"
    with patch("builtins.open", mock_open(read_data=contenido_invalido)):
        with pytest.raises(yaml.YAMLError):
            k8s_deploy.load_manifest("manifesto_invalido.yaml")


# tests para apply_manifest
@patch("src.k8s_deploy.client.AppsV1Api")
@patch("src.k8s_deploy.config.load_kube_config")
def test_aplica_manifest_deployment(mock_config, mock_api_class):
    manifest = {
        "kind": "Deployment",
        "metadata": {"name": "mi-deploy", "namespace": "default"}
    }
    mock_api = MagicMock()
    mock_api_class.return_value = mock_api
    resultado = k8s_deploy.apply_manifest(manifest)
    assert resultado is True
    mock_api.create_namespaced_deployment.assert_called_once()


@patch("src.k8s_deploy.client.AppsV1Api")
@patch("src.k8s_deploy.config.load_kube_config")
def test_aplica_manifest_tipo_no_soportado(mock_config, mock_api_class):
    manifest = {"kind": "Service"}
    resultado = k8s_deploy.apply_manifest(manifest)
    assert resultado is False


@patch("src.k8s_deploy.client.AppsV1Api", side_effect=k8s_deploy.ApiException("Error API"))
@patch("src.k8s_deploy.config.load_kube_config")
def test_error_api_al_aplicar_manifest(mock_config, mock_api_class):
    manifest = {"kind": "Deployment", "metadata": {"name": "x"}}
    resultado = k8s_deploy.apply_manifest(manifest)
    assert resultado is False


# tests para check_deployment_status
@patch("src.k8s_deploy.client.AppsV1Api")
@patch("src.k8s_deploy.config.load_kube_config")
def test_deployment_listo(mock_config, mock_api_class):
    mock_deploy = MagicMock()
    mock_deploy.status.ready_replicas = 3
    mock_deploy.spec.replicas = 3
    mock_api = MagicMock()
    mock_api.read_namespaced_deployment.return_value = mock_deploy
    mock_api_class.return_value = mock_api
    assert k8s_deploy.check_deployment_status("mi-deploy") is True


@patch("src.k8s_deploy.client.AppsV1Api")
@patch("src.k8s_deploy.config.load_kube_config")
def test_deployment_no_listo(mock_config, mock_api_class):
    mock_deploy = MagicMock()
    mock_deploy.status.ready_replicas = 1
    mock_deploy.spec.replicas = 3
    mock_api = MagicMock()
    mock_api.read_namespaced_deployment.return_value = mock_deploy
    mock_api_class.return_value = mock_api
    assert k8s_deploy.check_deployment_status("mi-deploy") is False


@patch("src.k8s_deploy.client.AppsV1Api", side_effect=k8s_deploy.ApiException("fallo"))
@patch("src.k8s_deploy.config.load_kube_config")
def test_error_leyendo_deployment(mock_config, mock_api_class):
    assert k8s_deploy.check_deployment_status("error") is False


# tests para flujo completo deploy
@patch("src.k8s_deploy.check_deployment_status", return_value=True)
@patch("src.k8s_deploy.apply_manifest", return_value=True)
@patch("src.k8s_deploy.load_manifest", return_value={"metadata": {"name": "test", "namespace": "default"}})
def test_deploy_exitoso(mock_load, mock_apply, mock_check):
    resultado = k8s_deploy.deploy("archivo.yaml")
    assert resultado is True
