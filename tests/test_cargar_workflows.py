import pytest
import os
import logging
import io
import sys
from src.event_engine import load_workflows


# fixture para capturar logs
@pytest.fixture
def capturar_log():
    # flujo que captura los logs
    flujo_log = io.StringIO()
    # configuracion del logger
    handler = logging.StreamHandler(flujo_log)
    # nivel de log
    handler.setLevel(logging.DEBUG)
    # formato del loger
    formato = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    # asignamos el formato al handler
    handler.setFormatter(formato)
    # creamos el logger
    yield flujo_log
    # cerramos el handler al finalizar
    handler.close()


# test para carga workflows validos
def test_cargar_workflows_valido(tmp_path, monkeypatch):
    # crea archivo workflows.yaml de prueba
    archi = tmp_path / "workflows.yaml"
    # escribe contenido
    archi.write_text("""
    workflows:
      - event: file_created
        path: /app/data
        action: /app/scripts/process_data.sh <file>
      - event: message_received
        queue: redis://redis:6379/0
        action: python /app/src/notify.py
    """)
    # simula que el archivo existe
    monkeypatch.setattr(os.path, "exists", lambda x: True)
    # carga los workflows
    workflows = load_workflows(str(archi))
    # verifica que cargaron correctamente
    assert len(workflows) == 2
    # verifica eventos coorrectos
    assert workflows[0]["event"] == "file_created"
    assert workflows[1]["event"] == "message_received"


# test para carga workflows faltante
def test_cargar_workflows_faltante(capturar_log, monkeypatch):
    # configura logger con ruta del archivo que no existe
    logger = logging.getLogger("src.event_engine")
    # limpiar handlers logger
    logger.handlers = []
    # nivel de log
    logger.setLevel(logging.ERROR)
    # asignar flujo log al logger
    logger.addHandler(logging.StreamHandler(capturar_log))
    # simular funcion open que lanza FileNotFoundError

    def mock_open(*args, **kwargs):
        raise FileNotFoundError("Archivo no existe")
    # reemplaza open por mock_open
    monkeypatch.setattr("builtins.open", mock_open)
    # reemplaza os.path.exists por funcion raise_system_exit
    monkeypatch.setattr(sys, "exit", lambda x: raise_system_exit(x))
    # funcion que lanza SystemExit

    def raise_system_exit(code):
        raise SystemExit(code)
    # se espera que se lance SystemExit despues dee cargar workflows
    with pytest.raises(SystemExit) as exc_info:
        load_workflows("/app/docs/workflows.yaml")
    # verifica que se lanza SystemExit
    assert exc_info.value.code == 1
    # captura el log
    log = capturar_log.getvalue()
    # verifica registro error en el log
    assert "No se encontro /app/docs/workflows.yaml" in log


# test para carga workflows invalido
def test_cargar_workflows_invalido(tmp_path, monkeypatch, capturar_log):
    # crea archivo workflows.yaml de prueba
    archi = tmp_path / "workflows.yaml"
    # escribe contenido invalido
    archi.write_text("invalid: yaml: content")
    # simula que el archivo existe
    monkeypatch.setattr(os.path, "exists", lambda x: True)
    # configura logger para capturar logs
    logger = logging.getLogger("src.event_engine")
    # limpiar handlers
    logger.handlers = []
    # nivel de log
    logger.setLevel(logging.ERROR)
    # asignar flujo log al logger
    logger.addHandler(logging.StreamHandler(capturar_log))
    # ejecuta carga workflows y espera SystemExit
    with pytest.raises(SystemExit):
        load_workflows(str(archi))
    # captura el log
    log = capturar_log.getvalue()
    # verifica error en  log
    assert "Error parseando" in log
