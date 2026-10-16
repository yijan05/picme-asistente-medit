"""La salud del backend informa la disponibilidad real de MySQL."""
import unittest
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
from backend.main import app


class BackendHealthTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    @patch("backend.main.get_connection")
    def test_health_check_con_base_conectada(self, get_connection):
        connection = Mock()
        connection.is_connected.return_value = True
        get_connection.return_value = connection
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "database": "connected"})
        connection.close.assert_called_once()

    @patch("backend.main.get_connection", side_effect=RuntimeError("Sin conexión"))
    def test_health_check_con_base_desconectada(self, get_connection):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "error", "database": "disconnected"})


if __name__ == "__main__":
    unittest.main()
