import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.auth import crear_access_token
from backend.main import app


class BackendBiometricApiTest(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

        self.user_token = crear_access_token(
            usuario_id=3,
            correo="hash.real@picme.test",
            rol="USER",
        )

        self.admin_token = crear_access_token(
            usuario_id=1,
            correo="admin@picme.test",
            rol="ADMIN",
        )

    def test_sin_token_rechaza_plantilla_biometrica(self):
        """El endpoint debe exigir autenticación."""

        response = self.client.post(
            "/biometric-templates",
            json={
                "usuario_id": 3,
                "ruta_svm": "data/models/usuario_3.pkl",
                "num_muestras": 25,
            },
        )

        self.assertEqual(response.status_code, 401)

    @patch("backend.main.guardar_plantilla_biometrica")
    def test_user_puede_guardar_su_propia_plantilla(
        self,
        mock_guardar,
    ):
        """USER debe poder guardar solamente su propia plantilla."""

        response = self.client.post(
            "/biometric-templates",
            headers={
                "Authorization": f"Bearer {self.user_token}",
            },
            json={
                "usuario_id": 3,
                "ruta_svm": "data/models/usuario_3.pkl",
                "num_muestras": 25,
            },
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(data["usuario_id"], 3)
        self.assertEqual(
            data["ruta_svm"],
            "data/models/usuario_3.pkl",
        )
        self.assertEqual(data["num_muestras"], 25)

        mock_guardar.assert_called_once_with(
            usuario_id=3,
            ruta_svm="data/models/usuario_3.pkl",
            num_muestras=25,
        )

    @patch("backend.main.guardar_plantilla_biometrica")
    def test_user_no_puede_guardar_plantilla_de_otro_usuario(
        self,
        mock_guardar,
    ):
        """USER debe recibir 403 al intentar guardar otra plantilla."""

        response = self.client.post(
            "/biometric-templates",
            headers={
                "Authorization": f"Bearer {self.user_token}",
            },
            json={
                "usuario_id": 99,
                "ruta_svm": "data/models/usuario_99.pkl",
                "num_muestras": 25,
            },
        )

        self.assertEqual(response.status_code, 403)

        self.assertEqual(
            response.json()["detail"],
            "Permisos insuficientes.",
        )

        mock_guardar.assert_not_called()

    @patch("backend.main.guardar_plantilla_biometrica")
    def test_admin_puede_guardar_plantilla_de_otro_usuario(
        self,
        mock_guardar,
    ):
        """ADMIN debe poder guardar cualquier plantilla."""

        response = self.client.post(
            "/biometric-templates",
            headers={
                "Authorization": f"Bearer {self.admin_token}",
            },
            json={
                "usuario_id": 99,
                "ruta_svm": "data/models/usuario_99.pkl",
                "num_muestras": 40,
            },
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(data["usuario_id"], 99)
        self.assertEqual(
            data["ruta_svm"],
            "data/models/usuario_99.pkl",
        )
        self.assertEqual(data["num_muestras"], 40)

        mock_guardar.assert_called_once_with(
            usuario_id=99,
            ruta_svm="data/models/usuario_99.pkl",
            num_muestras=40,
        )

    @patch("backend.main.guardar_plantilla_biometrica")
    def test_rechaza_usuario_id_invalido(
        self,
        mock_guardar,
    ):
        """No debe aceptar un usuario_id menor o igual a cero."""

        response = self.client.post(
            "/biometric-templates",
            headers={
                "Authorization": f"Bearer {self.user_token}",
            },
            json={
                "usuario_id": 0,
                "ruta_svm": "data/models/usuario_0.pkl",
                "num_muestras": 25,
            },
        )

        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            response.json()["detail"],
            "El usuario_id debe ser válido.",
        )

        mock_guardar.assert_not_called()

    @patch("backend.main.guardar_plantilla_biometrica")
    def test_rechaza_ruta_svm_vacia(
        self,
        mock_guardar,
    ):
        """No debe aceptar una ruta SVM vacía."""

        response = self.client.post(
            "/biometric-templates",
            headers={
                "Authorization": f"Bearer {self.user_token}",
            },
            json={
                "usuario_id": 3,
                "ruta_svm": "   ",
                "num_muestras": 25,
            },
        )

        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            response.json()["detail"],
            "La ruta_svm es obligatoria.",
        )

        mock_guardar.assert_not_called()

    @patch("backend.main.guardar_plantilla_biometrica")
    def test_rechaza_numero_de_muestras_negativo(
        self,
        mock_guardar,
    ):
        """No debe aceptar un número negativo de muestras."""

        response = self.client.post(
            "/biometric-templates",
            headers={
                "Authorization": f"Bearer {self.user_token}",
            },
            json={
                "usuario_id": 3,
                "ruta_svm": "data/models/usuario_3.pkl",
                "num_muestras": -1,
            },
        )

        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            response.json()["detail"],
            "El número de muestras no puede ser negativo.",
        )

        mock_guardar.assert_not_called()

    @patch("backend.main.obtener_plantilla_biometrica")
    def test_user_puede_consultar_su_propia_plantilla(
        self,
        mock_obtener,
    ):

        plantilla = {
            "usuario_id": 3,
            "ruta_svm": "data/models/usuario_3.pkl",
            "num_muestras": 25,
            "actualizado_en": None,
        }

        mock_obtener.return_value = plantilla

        response = self.client.get(
            "/biometric-templates/3",
            headers={
                "Authorization": f"Bearer {self.user_token}",
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.json(),
            {
                "usuario_id": 3,
                "ruta_svm": "data/models/usuario_3.pkl",
                "num_muestras": 25,
                "actualizado_en": None,
            },
        )

        mock_obtener.assert_called_once_with(3)

    @patch("backend.main.obtener_plantilla_biometrica")
    def test_user_no_puede_consultar_plantilla_de_otro_usuario(
        self,
        mock_obtener,
    ):
        """USER debe recibir 403 al consultar otra plantilla."""

        response = self.client.get(
            "/biometric-templates/99",
            headers={
                "Authorization": f"Bearer {self.user_token}",
            },
        )

        self.assertEqual(response.status_code, 403)

        self.assertEqual(
            response.json()["detail"],
            "Permisos insuficientes.",
        )

        mock_obtener.assert_not_called()

    @patch("backend.main.obtener_plantilla_biometrica")
    def test_admin_puede_consultar_plantilla_de_otro_usuario(
        self,
        mock_obtener,
    ):
        """ADMIN debe poder consultar cualquier plantilla."""

        plantilla = {
            "usuario_id": 99,
            "ruta_svm": "data/models/usuario_99.pkl",
            "num_muestras": 40,
            "actualizado_en": None,
        }

        mock_obtener.return_value = plantilla

        response = self.client.get(
            "/biometric-templates/99",
            headers={
                "Authorization": f"Bearer {self.admin_token}",
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.json(),
            {
                "usuario_id": 99,
                "ruta_svm": "data/models/usuario_99.pkl",
                "num_muestras": 40,
                "actualizado_en": None,
            },
        )

        mock_obtener.assert_called_once_with(99)

    @patch("backend.main.obtener_plantilla_biometrica")
    def test_consultar_plantilla_inexistente_devuelve_none(
        self,
        mock_obtener,
    ):
        """Una plantilla inexistente debe devolver null."""

        mock_obtener.return_value = None

        response = self.client.get(
            "/biometric-templates/3",
            headers={
                "Authorization": f"Bearer {self.user_token}",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json())

        mock_obtener.assert_called_once_with(3)

    @patch("backend.main.obtener_plantilla_biometrica")
    def test_consultar_plantilla_sin_token_rechaza_peticion(
        self,
        mock_obtener,
    ):
        """La consulta debe rechazar peticiones sin JWT."""

        response = self.client.get(
            "/biometric-templates/3",
        )

        self.assertEqual(response.status_code, 401)

        mock_obtener.assert_not_called()

    @patch("backend.main.obtener_plantilla_biometrica")
    def test_consultar_plantilla_con_usuario_id_invalido(
        self,
        mock_obtener,
    ):
        """No debe aceptar un usuario_id menor o igual a cero."""

        response = self.client.get(
            "/biometric-templates/0",
            headers={
                "Authorization": f"Bearer {self.user_token}",
            },
        )

        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            response.json()["detail"],
            "El usuario_id debe ser válido.",
        )

        mock_obtener.assert_not_called()

    @patch("backend.main.eliminar_plantilla_biometrica")
    def test_user_puede_eliminar_su_propia_plantilla(
        self,
        mock_eliminar,
    ):
        """USER debe poder eliminar su propia plantilla."""

        response = self.client.delete(
            "/biometric-templates/3",
            headers={
                "Authorization": f"Bearer {self.user_token}",
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.json(),
            {
                "usuario_id": 3,
                "eliminado": True,
            },
        )

        mock_eliminar.assert_called_once_with(3)

    @patch("backend.main.eliminar_plantilla_biometrica")
    def test_user_no_puede_eliminar_plantilla_de_otro_usuario(
        self,
        mock_eliminar,
    ):
        """USER debe recibir 403 al eliminar otra plantilla."""

        response = self.client.delete(
            "/biometric-templates/99",
            headers={
                "Authorization": f"Bearer {self.user_token}",
            },
        )

        self.assertEqual(response.status_code, 403)

        self.assertEqual(
            response.json()["detail"],
            "Permisos insuficientes.",
        )

        mock_eliminar.assert_not_called()

    @patch("backend.main.eliminar_plantilla_biometrica")
    def test_admin_puede_eliminar_plantilla_de_otro_usuario(
        self,
        mock_eliminar,
    ):
        """ADMIN debe poder eliminar cualquier plantilla."""

        response = self.client.delete(
            "/biometric-templates/99",
            headers={
                "Authorization": f"Bearer {self.admin_token}",
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.json(),
            {
                "usuario_id": 99,
                "eliminado": True,
            },
        )

        mock_eliminar.assert_called_once_with(99)

    @patch("backend.main.eliminar_plantilla_biometrica")
    def test_eliminar_plantilla_sin_token_rechaza_peticion(
        self,
        mock_eliminar,
    ):
        """La eliminación debe rechazar peticiones sin JWT."""

        response = self.client.delete(
            "/biometric-templates/3",
        )

        self.assertEqual(response.status_code, 401)

        mock_eliminar.assert_not_called()

    @patch("backend.main.eliminar_plantilla_biometrica")
    def test_eliminar_plantilla_con_usuario_id_invalido(
        self,
        mock_eliminar,
    ):
        """No debe aceptar un usuario_id menor o igual a cero."""

        response = self.client.delete(
            "/biometric-templates/0",
            headers={
                "Authorization": f"Bearer {self.user_token}",
            },
        )

        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            response.json()["detail"],
            "El usuario_id debe ser válido.",
        )

        mock_eliminar.assert_not_called()


if __name__ == "__main__":
    unittest.main()