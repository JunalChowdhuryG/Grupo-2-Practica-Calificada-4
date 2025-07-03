import pybreaker
import logging 
import subprocess

logger = logging.getLogger(__name__)

script_circuit_breaker = pybreaker.CircuitBreaker(
    fail_max=5,
    reset_timeout=60, 
    name="script_circuit_breaker",
    exclude=[KeyboardInterrupt]
)

class CircuitListener(pybreaker.CircuitBreakerListener):
    def state_change(self, cb, old_state, new_state):
        if new_state == 'open':
            logger.warning(f"Circuit breaker {cb.name} abierto luego de {cb.fail_max} fallos.")
        elif new_state == 'closed':
            logger.warning(f"Circuit breaker {cb.name} cerrado, listo para nuevas solicitudes.")


script_circuit_breaker.addListeners(CircuitListener())

@script_circuit_breaker
def safe_subprocess_run(command,**kwargs):
    logger.debug("Ejecutando comando de forma segura: %s", command)
    result = subprocess.run(command, **kwargs)
    if result.returncode != 0:
        logger.error("Comando fallido: %s", command)
        raise subprocess.CalledProcessError(result.returncode, command)
    return result