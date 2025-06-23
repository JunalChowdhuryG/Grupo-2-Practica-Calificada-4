import pytest
import logging
import io
from src.notify import notify


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
    # asignamos formato al handler
    handler.setFormatter(formato)
    # creamos  logger
    yield flujo_log
    # cerramos  handler al finalizar
    handler.close()


# test para notificar mensajes
def test_notificar_mensaje_valido(capturar_log):
    # logger para capturar los eventos
    logger = logging.getLogger("src.notify")
    # limpiar handler
    logger.handlers = []
    # nivel log
    logger.setLevel(logging.INFO)
    # se dirige log al flujo capturado
    logger.addHandler(logging.StreamHandler(capturar_log))
    # notificar mensaje
    notify("Mensaje de prueba")
    # capturamos log
    log = capturar_log.getvalue()
    # verifica mensaje log
    assert "Received message: Mensaje de prueba" in log


# test para notificar mensaje de default
def test_notificar_mensaje_default(capturar_log):
    # logger para capturar los eventos
    logger = logging.getLogger("src.notify")
    # limpiar handler
    logger.handlers = []
    # nivel log
    logger.setLevel(logging.INFO)
    # se dirige log al flujo capturado
    logger.addHandler(logging.StreamHandler(capturar_log))
    # notificar mensaje por defaul
    notify()
    # capturamos log
    log = capturar_log.getvalue()
    # verifica mensaje log
    assert "Received message: Test message" in log
