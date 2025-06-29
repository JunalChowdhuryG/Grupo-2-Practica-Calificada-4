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
    # formato del logger
    formato = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    # asignamos el formato al handler
    handler.setFormatter(formato)
    # creamos el logger
    logger = logging.getLogger("src.event_engine")
    logger.handlers = []
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    yield flujo_log
    # cerramos el handler al finalizar
    handler.close()


# test para manejar eventos de archivos con accion script
def test_manejador_eventos_archivo_valido_script(monkeypatch, capturar_log):
    # flujo para la creacion de archivos
    workflows = [
        {
            "id": "process_file",
            "event": "file_created",
            "path": "/app/data",
            "action_type": "script",
            "action": "/app/scripts/process_data.sh <file>",
            "recursive": True
        }
    ]
    # creamos objeto del manejador de eventos
    handler = FileEventHandler(workflows)
    # simula subprocess.run para evitar ejecuciones reales
    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: type("Result", (), {"returncode": 0})())
    # simula check_dependencies para que devuelva True
    monkeypatch.setattr("src.workflow_deps.check_dependencies", lambda x: True)
    # creamos evento simulado
    evento = type("Event", (), {"src_path": "/app/data/test.txt", "is_directory": False})()
    # metodo manejar el evento
    handler.on_created(evento)
    # capturamos el log
    log = capturar_log.getvalue()
    # verifica los logs son correctos
    assert "Archivo creado: /app/data/test.txt" in log
    assert "Ejecutando acción: /app/scripts/process_data.sh /app/data/test.txt" in log


# test para manejar eventos con recursive false
def test_manejador_eventos_recursive_false(monkeypatch, capturar_log):
    # flujo para la creacion de archivos
    workflows = [
        {
            "id": "process_file",
            "event": "file_created",
            "path": "/app/data",
            "action_type": "script",
            "action": "/app/scripts/process_data.sh <file>",
            "recursive": False
        }
    ]
    # creamos objeto del manejador de eventos
    handler = FileEventHandler(workflows)
    # simula subprocess.run para evitar ejecuciones reales
    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: type("Result", (), {"returncode": 0})())
    # simula check_dependencies para que devuelva True
    monkeypatch.setattr("src.workflow_deps.check_dependencies", lambda x: True)
    # creamos evento simulado en un subdirectorio
    evento = type("Event", (), {"src_path": "/app/data/subdir/test.txt", "is_directory": False})()
    # metodo manejar el evento
    handler.on_created(evento)
    # capturamos el log
    log = capturar_log.getvalue()
    # verifica que no se ejecuta la accion
    assert "Archivo creado: /app/data/subdir/test.txt" in log
    assert "Ejecutando acción" not in log
