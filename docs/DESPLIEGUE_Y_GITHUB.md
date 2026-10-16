# Publicación y conexión real

## Activar Gemini en tu PC

1. Dentro de `desktop`, abre `CONFIGURAR_GEMINI.bat`.
2. Se abre un archivo `.env` local. Completa `GEMINI_API_KEY` con tu clave y guarda.
3. El valor inicial de `GEMINI_MODEL` es `gemini-3.8-flash`, configurable si tu cuenta requiere otro modelo compatible.
4. Ejecuta `VERIFICAR_LLM.bat`. La prueba falla si la respuesta solo procede de la base local.
5. Abre `SOLO_CHATBOT.bat` o `INICIAR_PICME.bat` y consulta un principio.

La clave se obtiene y administra en [Google AI Studio](https://aistudio.google.com/api-keys). El archivo `.env` queda fuera del control de versiones.

## Activar Gemini en la nube

El backend necesita `GEMINI_API_KEY` como secreto de ejecución y, opcionalmente, `GEMINI_MODEL` como variable. Configura estos valores en el servicio que aloja el servidor y aplica una nueva versión de despliegue. El navegador nunca debe recibir la clave.

Comprueba una pregunta desde la web. La respuesta debe llevar la etiqueta **Gemini**; el indicador de configuración, una respuesta del modo local o un test simulado no sustituyen esta prueba.

El sitio empieza con acceso privado. Para entregar el enlace, verifica con una cuenta que represente al docente que tiene acceso. No presentes un enlace privado inaccesible para él como un despliegue evaluable.

## Repositorio público de GitHub

La cuenta conectada no expuso repositorios accesibles durante esta preparación. No se creó un repositorio público ni se inventó un enlace.

1. Crea un repositorio vacío y **público** desde [GitHub](https://github.com/new). Puedes llamarlo `picme-asistente-medit`. No añadas README desde GitHub si vas a importar el historial.
2. Copia la URL HTTPS del repositorio que realmente creaste.
3. El paquete de entrega contiene la fuente y, cuando se incluye `historial.bundle`, el historial de Git preparado. Abre `PUBLICAR_GITHUB.bat` y escribe la URL real. Git puede pedirte iniciar sesión mediante su gestor de credenciales. También puedes ejecutar:

```powershell
py -3.10 publicar_github.py --repo "URL_HTTPS_DE_TU_REPOSITORIO"
```

La URL del ejemplo es un marcador, no un repositorio existente. El script crea un clon nuevo, conserva el historial del bundle y no hace pushes forzados. Publica la versión preparada en el bundle; si haces cambios después, aplícalos al clon antes de crear otro commit.

4. Abre GitHub sin sesión y verifica que aparecen el README, los archivos del proveedor, el prompt, la base contextual y las pruebas.
5. Actualiza en el README la URL real del repositorio y la del video después de grabarlo.

No se incluyen bases de usuarios, fotografías, plantillas de rostros ni claves en el paquete publicable. La base de conocimiento pública se reconstruye al iniciar el programa.

## Fuentes técnicas

- [Gemini: generación y system instructions](https://ai.google.dev/api/generate-content).
- [Uso seguro de claves de Gemini](https://ai.google.dev/gemini-api/docs/api-key).
- [Modelo Gemini 3.8 Flash](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash).
