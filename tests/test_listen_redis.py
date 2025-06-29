import pytest
import logging
import io
from src.event_engine import listen_redis
import redis


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


# test verifica escuchar mensajes de redis
def test_escuchar_redis_valido(monkeypatch, capturar_log):
    # define workflows para recibir mensaje por redis
    workflows = [
        {
            "event": "message_received",
            "queue": "redis://redis:6379/0",
            "action_type": "script",
            "action": "python /app/src/notify.py",
        }
    ]

    # mock para simular redis
    class MockRedis:
        def __init__(self):
            self.pubsub_instance = MockPubSub()

        def pubsub(self):
            return self.pubsub_instance

    # mock para simular comportamiento de pubsub de redis
    class MockPubSub:
        # simula suscripcion
        def subscribe(self, *args):
            pass

        # simula recibir mensaje
        def listen(self):
            return [{"type": "message", "data": "Hola"}]
    # reemplaza Redis.from_url por mock
    monkeypatch.setattr("redis.Redis.from_url", lambda *args, **kwargs: MockRedis())
    # reemplaza subprocess.run para evitar ejecucion comandos externos
    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: type("Result", (), {"returncode": 0})())
    # ejecuta funcion listen_redis con workflows
    try:
        listen_redis("redis://redis:6379/0", workflows)
    # evita bucles infinitos
    except StopIteration:
        pass
    # captura logs
    log = capturar_log.getvalue()
    # verifica que los logs contienen la informacion esperada
    assert "Suscrito a Redis queue: redis://redis:6379/0" in log
    assert "Mensaje recibido: Hola" in log
    assert "Ejecutando accion: python /app/src/notify.py" in log


# test para error de redis
def test_escuchar_redis_error(monkeypatch, capturar_log):
    # funcion simula error de redis al conectar
    def raise_redis_error(*args, **kwargs):
        raise redis.RedisError("Connection failed")
    # reemplaza Redis.from_url para simular error
    monkeypatch.setattr("redis.Redis.from_url", raise_redis_error)
    # configura logger para capturar logs
    logger = logging.getLogger("src.event_engine")
    logger.handlers = []
    logger.setLevel(logging.ERROR)
    logger.addHandler(logging.StreamHandler(capturar_log))
    # se espera que se lance SystemExit al intentar escuchar redis
    with pytest.raises(SystemExit):
        listen_redis("redis://redis:6379/0", [])
    # captura log
    log = capturar_log.getvalue()
    # verifica mensaje de error en log
    assert "Error de Redis: Connection failed" in log
