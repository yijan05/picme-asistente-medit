"""
Pruebas de autenticación y autorización JWT
del backend de PicMe.
"""

from datetime import datetime, timedelta, timezone
import unittest
from unittest.mock import patch

import jwt
from fastapi.testclient import TestClient
from werkzeug.security import generate_password_hash

from backend.auth import (
    crear_access_token,
    verificar_access_token,
    verificar_rol,
)
from backend.config import JWT_ALGORITHM, JWT_SECRET
from backend.main import app


class BackendAuthTest(unittest.TestCase):
    """Pruebas de autenticación y autorización mediante JWT."""

    def setUp(self):
        self.client = TestClient(app)

        self.token = crear_access_token(
            usuario_id=3,
            correo="hash.real@picme.test",
            rol="USER",
        )

        self.headers = {
            "Authorization": f"Bearer {self.token}",
        }

    def test_crear_y_verificar_access_token(self):
        """Un token creado por el backend debe poder verificarse."""

        token = crear_access_token(
            usuario_id=123,
            correo="usuario@picme.test",
            rol="USER",
        )

        payload = verificar_access_token(token)

        self.assertEqual(payload["sub"], "123")
        self.assertEqual(
            payload["correo"],
            "usuario@picme.test",
        )
        self.assertEqual(payload["rol"], "USER")
        self.assertIn("iat", payload)
        self.assertIn("exp", payload)

    def test_login_devuelve_jwt(self):
        """Un login correcto debe devolver un access_token JWT."""

        password = "MiPassword123"

        usuario = {
            "id": 3,
            "nombre": "Usuario Hash Real",
            "correo": "hash.real@picme.test",
            "password_hash": generate_password_hash(password),
            "rol": "USER",
        }

        with patch(
            "backend.main.obtener_usuario_por_correo",
            return_value=usuario,
        ):
            response = self.client.post(
                "/auth/login",
                json={
                    "correo": usuario["correo"],
                    "password_hash": password,
                },
            )

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertIn("access_token", data)
        self.assertEqual(
            data["token_type"],
            "bearer",
        )
        self.assertEqual(data["id"], 3)
        self.assertEqual(
            data["correo"],
            "hash.real@picme.test",
        )
        self.assertEqual(data["rol"], "USER")

        payload = jwt.decode(
            data["access_token"],
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
        )

        self.assertEqual(payload["sub"], "3")
        self.assertEqual(
            payload["correo"],
            "hash.real@picme.test",
        )
        self.assertEqual(payload["rol"], "USER")

    def test_login_con_password_incorrecto(self):
        """Una contraseña incorrecta debe rechazar el login."""

        usuario = {
            "id": 3,
            "nombre": "Usuario Hash Real",
            "correo": "hash.real@picme.test",
            "password_hash": generate_password_hash(
                "MiPassword123"
            ),
            "rol": "USER",
        }

        with patch(
            "backend.main.obtener_usuario_por_correo",
            return_value=usuario,
        ):
            response = self.client.post(
                "/auth/login",
                json={
                    "correo": usuario["correo"],
                    "password_hash": "PasswordIncorrecto",
                },
            )

        self.assertEqual(response.status_code, 401)

        self.assertEqual(
            response.json()["detail"],
            "Credenciales inválidas.",
        )

    @patch(
        "backend.main.listar_usuarios",
        return_value=[],
    )
    def test_users_sin_token_rechaza_peticion(
        self,
        mock_listar_usuarios,
    ):
        """GET /users debe rechazar peticiones sin JWT."""

        response = self.client.get("/users")

        self.assertEqual(response.status_code, 401)

        self.assertEqual(
            response.json()["detail"],
            "Autenticación requerida.",
        )

        mock_listar_usuarios.assert_not_called()

    @patch(
        "backend.main.listar_usuarios",
        return_value=[],
    )
    def test_users_con_token_invalido_rechaza_peticion(
        self,
        mock_listar_usuarios,
    ):
        """GET /users debe rechazar un JWT inválido."""

        response = self.client.get(
            "/users",
            headers={
                "Authorization": "Bearer token-invalido",
            },
        )

        self.assertEqual(response.status_code, 401)

        self.assertEqual(
            response.json()["detail"],
            "Token inválido o expirado.",
        )

        mock_listar_usuarios.assert_not_called()

    @patch(
        "backend.main.listar_usuarios",
        return_value=[],
    )
    def test_users_con_token_user_rechaza_peticion(
        self,
        mock_listar_usuarios,
    ):
        """GET /users debe rechazar a un usuario USER."""

        response = self.client.get(
            "/users",
            headers=self.headers,
        )

        self.assertEqual(response.status_code, 403)

        self.assertEqual(
            response.json()["detail"],
            "Permisos insuficientes.",
        )

        mock_listar_usuarios.assert_not_called()

    @patch(
        "backend.main.listar_usuarios",
        return_value=[],
    )
    def test_users_con_token_admin_permite_peticion(
        self,
        mock_listar_usuarios,
    ):
        """GET /users debe permitir a un usuario ADMIN."""

        token = crear_access_token(
            usuario_id=1,
            correo="admin@picme.test",
            rol="ADMIN",
        )

        response = self.client.get(
            "/users",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

        mock_listar_usuarios.assert_called_once()

    @patch(
        "backend.main.listar_usuarios",
        return_value=[],
    )
    def test_users_con_token_expirado_rechaza_peticion(
        self,
        mock_listar_usuarios,
    ):
        """GET /users debe rechazar un JWT expirado."""

        ahora = datetime.now(timezone.utc)

        payload = {
            "sub": "3",
            "correo": "hash.real@picme.test",
            "rol": "ADMIN",
            "iat": ahora - timedelta(minutes=10),
            "exp": ahora - timedelta(minutes=5),
        }

        token = jwt.encode(
            payload,
            JWT_SECRET,
            algorithm=JWT_ALGORITHM,
        )

        response = self.client.get(
            "/users",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        self.assertEqual(response.status_code, 401)

        self.assertEqual(
            response.json()["detail"],
            "Token inválido o expirado.",
        )

        mock_listar_usuarios.assert_not_called()

    @patch(
        "backend.main.obtener_usuario_por_id",
        return_value={
            "id": 3,
            "nombre": "Usuario Hash Real",
            "correo": "hash.real@picme.test",
            "rol": "USER",
            "creado_en": None,
            "password_hash": "hash",
        },
    )
    def test_user_por_id_sin_token_rechaza_peticion(
        self,
        mock_obtener_usuario,
    ):
        """GET /users/{id} debe rechazar peticiones sin JWT."""

        response = self.client.get("/users/3")

        self.assertEqual(response.status_code, 401)

        self.assertEqual(
            response.json()["detail"],
            "Autenticación requerida.",
        )

        mock_obtener_usuario.assert_not_called()

    @patch(
        "backend.main.obtener_usuario_por_id",
        return_value={
            "id": 3,
            "nombre": "Usuario Hash Real",
            "correo": "hash.real@picme.test",
            "rol": "USER",
            "creado_en": None,
            "password_hash": "hash",
        },
    )
    def test_user_por_id_con_token_valido_permite_peticion(
        self,
        mock_obtener_usuario,
    ):
        """GET /users/{id} debe aceptar un JWT válido."""

        response = self.client.get(
            "/users/3",
            headers=self.headers,
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(data["id"], 3)
        self.assertEqual(
            data["correo"],
            "hash.real@picme.test",
        )

        self.assertNotIn(
            "password_hash",
            data,
        )

        mock_obtener_usuario.assert_called_once_with(3)

    @patch(
        "backend.main.obtener_usuario_por_correo",
        return_value={
            "id": 3,
            "nombre": "Usuario Hash Real",
            "correo": "hash.real@picme.test",
            "rol": "USER",
            "creado_en": None,
            "password_hash": "hash",
        },
    )
    def test_user_por_email_sin_token_rechaza_peticion(
        self,
        mock_obtener_usuario,
    ):
        """GET /users/by-email/{correo} requiere JWT."""

        response = self.client.get(
            "/users/by-email/hash.real@picme.test"
        )

        self.assertEqual(response.status_code, 401)

        self.assertEqual(
            response.json()["detail"],
            "Autenticación requerida.",
        )

        mock_obtener_usuario.assert_not_called()

    @patch(
        "backend.main.obtener_usuario_por_correo",
        return_value={
            "id": 3,
            "nombre": "Usuario Hash Real",
            "correo": "hash.real@picme.test",
            "rol": "USER",
            "creado_en": None,
            "password_hash": "hash",
        },
    )
    def test_user_por_email_con_token_valido_permite_peticion(
        self,
        mock_obtener_usuario,
    ):
        """GET /users/by-email/{correo} acepta un JWT válido."""

        response = self.client.get(
            "/users/by-email/hash.real@picme.test",
            headers=self.headers,
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(data["id"], 3)
        self.assertEqual(
            data["correo"],
            "hash.real@picme.test",
        )

        self.assertNotIn(
            "password_hash",
            data,
        )

        mock_obtener_usuario.assert_called_once_with(
            "hash.real@picme.test"
        )

    @patch(
        "backend.main.crear_usuario",
        return_value=10,
    )
    def test_crear_user_sin_token_rechaza_peticion(
        self,
        mock_crear_usuario,
    ):
        """POST /users debe rechazar peticiones sin JWT."""

        response = self.client.post(
            "/users",
            json={
                "nombre": "Nuevo Usuario",
                "correo": "nuevo@picme.test",
                "password_hash": "MiPassword123",
                "rol": "USER",
            },
        )

        self.assertEqual(response.status_code, 401)

        self.assertEqual(
            response.json()["detail"],
            "Autenticación requerida.",
        )

        mock_crear_usuario.assert_not_called()

    @patch(
        "backend.main.crear_usuario",
        return_value=10,
    )
    def test_crear_user_con_token_admin_permite_peticion(
        self,
        mock_crear_usuario,
    ):
        """POST /users requiere un JWT válido de administrador."""

        token_admin = crear_access_token(
            usuario_id=3,
            correo="admin@picme.test",
            rol="ADMIN",
        )

        response = self.client.post(
            "/users",
            headers={"Authorization": f"Bearer {token_admin}"},
            json={
                "nombre": "Nuevo Usuario",
                "correo": "nuevo@picme.test",
                "password_hash": "MiPassword123",
                "rol": "USER",
            },
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(data["id"], 10)
        self.assertEqual(
            data["nombre"],
            "Nuevo Usuario",
        )
        self.assertEqual(
            data["correo"],
            "nuevo@picme.test",
        )
        self.assertEqual(
            data["rol"],
            "USER",
        )

        mock_crear_usuario.assert_called_once()

        argumentos = mock_crear_usuario.call_args.kwargs

        self.assertEqual(
            argumentos["nombre"],
            "Nuevo Usuario",
        )
        self.assertEqual(
            argumentos["correo"],
            "nuevo@picme.test",
        )
        self.assertEqual(
            argumentos["rol"],
            "USER",
        )

        self.assertNotEqual(
            argumentos["password_hash"],
            "MiPassword123",
        )

    def test_verificar_rol_user_permitido(self):
        """Un usuario USER debe ser aceptado cuando USER está permitido."""

        payload = {
            "sub": "3",
            "correo": "user@picme.test",
            "rol": "USER",
        }

        resultado = verificar_rol(
            payload,
            {"USER"},
        )

        self.assertEqual(
            resultado,
            payload,
        )

    def test_verificar_rol_admin_permitido(self):
        """Un usuario ADMIN debe ser aceptado cuando ADMIN está permitido."""

        payload = {
            "sub": "1",
            "correo": "admin@picme.test",
            "rol": "ADMIN",
        }

        resultado = verificar_rol(
            payload,
            {"ADMIN"},
        )

        self.assertEqual(
            resultado,
            payload,
        )

    def test_verificar_rol_acepta_cualquiera_de_los_roles_permitidos(self):
        """La autorización puede permitir varios roles."""

        payload_user = {
            "sub": "3",
            "correo": "user@picme.test",
            "rol": "USER",
        }

        payload_admin = {
            "sub": "1",
            "correo": "admin@picme.test",
            "rol": "ADMIN",
        }

        self.assertEqual(
            verificar_rol(
                payload_user,
                {"USER", "ADMIN"},
            ),
            payload_user,
        )

        self.assertEqual(
            verificar_rol(
                payload_admin,
                {"USER", "ADMIN"},
            ),
            payload_admin,
        )

    def test_verificar_rol_user_no_permitido(self):
        """USER debe ser rechazado cuando solamente ADMIN está permitido."""

        payload = {
            "sub": "3",
            "correo": "user@picme.test",
            "rol": "USER",
        }

        with self.assertRaises(PermissionError) as contexto:
            verificar_rol(
                payload,
                {"ADMIN"},
            )

        self.assertEqual(
            str(contexto.exception),
            "El usuario no tiene permisos suficientes.",
        )

    def test_verificar_rol_admin_no_permitido(self):
        """ADMIN debe ser rechazado cuando solamente USER está permitido."""

        payload = {
            "sub": "1",
            "correo": "admin@picme.test",
            "rol": "ADMIN",
        }

        with self.assertRaises(PermissionError) as contexto:
            verificar_rol(
                payload,
                {"USER"},
            )

        self.assertEqual(
            str(contexto.exception),
            "El usuario no tiene permisos suficientes.",
        )

    def test_verificar_rol_sin_rol_rechaza_peticion(self):
        """Un payload sin rol debe ser rechazado."""

        payload = {
            "sub": "3",
            "correo": "user@picme.test",
        }

        with self.assertRaises(PermissionError) as contexto:
            verificar_rol(
                payload,
                {"USER"},
            )

        self.assertEqual(
            str(contexto.exception),
            "El usuario no tiene un rol válido.",
        )

    def test_verificar_rol_con_rol_desconocido_rechaza_peticion(self):
        """Un rol desconocido debe ser rechazado."""

        payload = {
            "sub": "3",
            "correo": "user@picme.test",
            "rol": "SUPERADMIN",
        }

        with self.assertRaises(PermissionError) as contexto:
            verificar_rol(
                payload,
                {"SUPERADMIN"},
            )

        self.assertEqual(
            str(contexto.exception),
            "El usuario no tiene un rol válido.",
        )

    def test_verificar_rol_normaliza_el_rol(self):
        """El rol debe normalizarse antes de comprobar los permisos."""

        payload = {
            "sub": "3",
            "correo": "user@picme.test",
            "rol": " user ",
        }

        resultado = verificar_rol(
            payload,
            {"USER"},
        )

        self.assertEqual(
            resultado,
            payload,
        )


if __name__ == "__main__":
    unittest.main()
