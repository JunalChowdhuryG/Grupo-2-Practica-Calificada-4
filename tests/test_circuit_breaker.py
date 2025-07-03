import pytest
import pybreaker
from src.circuit_breakers import script_circuit_breaker, CircuitListener, safe_subprocess_run
import subprocess

def test_script_circuit_breaker():
    
    script_circuit_breaker.close()

    failing_commands = ["exit 1"] * 5 

    for i in range(4):
        with pytest.raises(subprocess.CalledProcessError):
            safe_subprocess_run(failing_commands[i], shell=True)

    with pytest.raises(pybreaker.CircuitBreakerError):
        safe_subprocess_run(failing_commands[4], shell=True)

def test_succesful_script():
    script_circuit_breaker.close()

    result = safe_subprocess_run("echo 'Hello World'", shell=True, capture_output=True, text=True)
    assert result.returncode == 0
    assert result.stdout.strip() == "Hello World"

