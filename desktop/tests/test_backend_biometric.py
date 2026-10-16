import unittest
from unittest.mock import MagicMock, patch

from backend.biometric_repository import (
    eliminar_plantilla_biometrica,
    guardar_plantilla_biometrica,
    obtener_plantilla_biometrica,
)


class BackendBiometricRepositoryTest(unittest.TestCase):

    @patch("backend.biometric_repository.get_connection")
    def test_guardar_plantilla_biometrica(
        self,
        mock_get_connection,
    ):
        """Debe guardar una plantilla biométrica y confirmar la transacción."""

        connection = MagicMock()
        cursor = MagicMock()

        mock_get_connection.return_value = connection
        connection.cursor.return_value = cursor

        guardar_plantilla_biometrica(
            usuario_id=3,
            ruta_svm="data/models/usuario_3.pkl",
            num_muestras=25,
        )

        cursor.execute.assert_called_once()

        argumentos = cursor.execute.call_args

        self.assertEqual(
            argumentos.args[1],
            (
                3,
                "data/models/usuario_3.pkl",
                25,
            ),
        )

        connection.commit.assert_called_once()
        cursor.close.assert_called_once()
        connection.close.assert_called_once()

    @patch("backend.biometric_repository.get_connection")
    def test_obtener_plantilla_biometrica_existente(
        self,
        mock_get_connection,
    ):
        """Debe devolver la plantilla biométrica cuando existe."""

        connection = MagicMock()
        cursor = MagicMock()

        plantilla = {
            "usuario_id": 3,
            "ruta_svm": "data/models/usuario_3.pkl",
            "num_muestras": 25,
            "actualizado_en": None,
        }

        mock_get_connection.return_value = connection
        connection.cursor.return_value = cursor
        cursor.fetchone.return_value = plantilla

        resultado = obtener_plantilla_biometrica(3)

        self.assertEqual(
            resultado,
            plantilla,
        )

        cursor.execute.assert_called_once_with(
            """
            SELECT
                usuario_id,
                ruta_svm,
                num_muestras,
                actualizado_en
            FROM biometric_templates
            WHERE usuario_id = %s
            LIMIT 1
            """,
            (3,),
        )

        cursor.close.assert_called_once()
        connection.close.assert_called_once()

    @patch("backend.biometric_repository.get_connection")
    def test_obtener_plantilla_biometrica_inexistente(
        self,
        mock_get_connection,
    ):
        """Debe devolver None cuando el usuario no tiene plantilla."""

        connection = MagicMock()
        cursor = MagicMock()

        mock_get_connection.return_value = connection
        connection.cursor.return_value = cursor
        cursor.fetchone.return_value = None

        resultado = obtener_plantilla_biometrica(99)

        self.assertIsNone(resultado)

        cursor.execute.assert_called_once_with(
            """
            SELECT
                usuario_id,
                ruta_svm,
                num_muestras,
                actualizado_en
            FROM biometric_templates
            WHERE usuario_id = %s
            LIMIT 1
            """,
            (99,),
        )

        cursor.close.assert_called_once()
        connection.close.assert_called_once()

    @patch("backend.biometric_repository.get_connection")
    def test_eliminar_plantilla_biometrica(
        self,
        mock_get_connection,
    ):
        """Debe eliminar la plantilla y confirmar la transacción."""

        connection = MagicMock()
        cursor = MagicMock()

        mock_get_connection.return_value = connection
        connection.cursor.return_value = cursor

        eliminar_plantilla_biometrica(3)

        cursor.execute.assert_called_once_with(
            """
            DELETE FROM biometric_templates
            WHERE usuario_id = %s
            """,
            (3,),
        )

        connection.commit.assert_called_once()
        cursor.close.assert_called_once()
        connection.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()