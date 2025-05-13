import subprocess
from shlex import split

from flask import Config
from ..core.exceptions import SecurityError

class CommandService:
    def __init__(self, allowed_commands):
        self.allowed_commands = allowed_commands

    def execute(self, command: str) -> dict:
        # Валидация команды
        if not self._is_command_allowed(command):
            raise SecurityError(f"Command not allowed: {command}")
        
        # Выполнение
        try:
            result = subprocess.run(
                split(command),
                capture_output=True,
                text=True,
                timeout=Config.COMMAND_TIMEOUT
            )
            return {
                "output": result.stdout,
                "error": result.stderr,
                "code": result.returncode
            }
        except Exception as e:
            raise RuntimeError(f"Command failed: {str(e)}")

    def _is_command_allowed(self, command: str) -> bool:
        base_cmd = command.split()[0]
        return base_cmd in self.allowed_commands