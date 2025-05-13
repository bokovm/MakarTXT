import pytest
from app.modules.system.service import CommandService
from app.core.exceptions import SecurityError

class TestCommandService:
    @pytest.fixture
    def service(self):
        return CommandService(allowed_commands=['ls', 'dir'])

    def test_allowed_command(self, service):
        result = service.execute("ls -l")
        assert "total" in result['output']

    def test_blocked_command(self, service):
        with pytest.raises(SecurityError):
            service.execute("rm -rf /")