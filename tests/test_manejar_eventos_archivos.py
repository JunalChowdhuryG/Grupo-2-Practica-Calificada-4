import pytest
import logging
import io
from src.event_engine import FileEventHandler


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


# test para manejar eventos de archivos
def test_manejador_eventos_archivo_valido(monkeypatch, capturar_log):
    # flujo para la creacion de archivos
    workflows = [
        {
            "event": "file_created",
            "path": "/app/data",
            "action": "/app/scripts/process_data.sh <file>",
        }
    ]
    # logger para capturar los eventos
    logger = logging.getLogger("src.event_engine")
    # limpiar los handler
    logger.handlers = []
    # nivel de log
    logger.setLevel(logging.DEBUG)
    # se dirige el log al flujo capturado
    logger.addHandler(logging.StreamHandler(capturar_log))
    # creamos objeto del manejador de eventos
    handler = FileEventHandler(workflows)
    # para evitar ejecuciones reales
    monkeypatch.setattr("os.system", lambda x: None)
    # creamos  evento simulado
    evento = type("Event", (), {"src_path": "/app/data/test5.txt", "is_directory": False})()
    # metodo manejar el evento
    handler.on_created(evento)
    # capturamos el log
    log = capturar_log.getvalue()
    # verifica los log son correctos
    assert "Archivo creado: /app/data/test5.txt" in log
    assert "Ejecutando accion: /app/scripts/process_data.sh /app/data/test5.txt" in log


# test para manejar eventos de archivos en directorios
def test_manejador_eventos_archivo_directorio(monkeypatch, capturar_log):
    # flujo para la creacion de archivos
    workflows = [
        {
            "event": "file_created",
            "path": "/app/data",
            "action": "/app/scripts/process_data.sh <file>",
        }
    ]
    # logger para capturar los eventos
    logger = logging.getLogger("src.event_engine")
    # limpiar los handler
    logger.handlers = []
    # nivel de log
    logger.setLevel(logging.DEBUG)
    # se dirige el log al flujo capturado
    logger.addHandler(logging.StreamHandler(capturar_log))
    # creamos objeto del manejador de eventos
    handler = FileEventHandler(workflows)
    # para evitar ejecuciones reales
    monkeypatch.setattr("os.system", lambda x: None)
    # creamos evento simulado para un directorio
    event = type("Event", (), {"src_path": "/app/data/subdir", "is_directory": True})()
    # metodo manejar el evento
    handler.on_created(event)
    # capturamos el log
    log = capturar_log.getvalue()
    # verifica que no se ha creado un archivo
    assert "Archivo creado" not in log
