# Actualización del chatbot de escritorio

Esta actualización agrega las consultas de registros de PicMe y las respuestas en inglés, conservando las correcciones anteriores sobre la Declaración Persona Transhumana.

## Cómo instalar la actualización

1. Cierra PicMe si está abierto.
2. Extrae `PicMe_Chatbot_Correcciones_Integradas.zip`.
3. Entra a `Archivos_para_GitHub/desktop` y copia su contenido en la carpeta `desktop` de tu instalación de PicMe. Acepta reemplazar los archivos existentes.
4. Ejecuta `ACTUALIZAR_BD.bat`. Debe indicar que hay **33 artículos y seis fuentes**.
5. Ejecuta `INICIAR_PICME.bat` y abre el chatbot.

Si necesitas ejecutar los comandos manualmente desde PowerShell, entra primero a la carpeta `desktop`:

```powershell
& ".\.venv\Scripts\python.exe" .\actualizar_conocimiento.py
& ".\.venv\Scripts\python.exe" .\run.py
```

La actualización conserva el archivo `.env`, el entorno instalado y los registros de estudiantes de tu PC, siempre que no los reemplaces ni los elimines.

## Cómo comprobar que funciona

Prueba estas preguntas en el chatbot:

| Pregunta | Resultado esperado |
|---|---|
| ¿Cuántas personas están registradas en PicMe? | Muestra el total de registros de la base de datos local. |
| How many people are registered in PicMe? | Muestra el total en inglés. |
| ¿Cuál fue mi último ingreso? | Consulta la sesión actual o solicita iniciar sesión. |
| Explain principle 6 | Explica el principio en inglés y muestra su fuente. |
| como se si soy una persona tras humana | Ofrece una reflexión sobre la declaración sin definir la identidad del usuario. |

Las consultas de registros se realizan directamente en SQLite y son de solo lectura. Por eso, pueden funcionar incluso cuando Gemini está activado o no está disponible. Las preguntas educativas utilizan Gemini cuando está configurado y funciona correctamente.

## Permisos para consultar datos de otras personas

Para autorizar una cuenta a consultar el historial o la fecha de registro de otras personas, agrega su correo a tu archivo `.env`:

```env
PICME_CHATBOT_ADMIN_EMAILS=correo_de_tu_cuenta_registrada
```

Puedes incluir varios correos separados por comas. Después, reinicia PicMe e inicia sesión con una cuenta autorizada.

## Actualizar el repositorio de GitHub

1. Copia el contenido de `Archivos_para_GitHub` en tu carpeta local del repositorio.
2. Acepta reemplazar los archivos correspondientes.
3. Abre PowerShell y ejecuta:

```powershell
cd "C:\Users\yijan\Downloads\PicMe_GitHub"
git add desktop README.md docs/ACTUALIZACION_CHATBOT.md
git commit -m "Integrar consultas de PicMe y respuestas bilingues"
git push origin main
```

**Importante:** utiliza únicamente los archivos preparados para GitHub. El ZIP original de la instalación puede contener `.env`, bases de datos locales, claves de cifrado y el entorno `.venv`. No publiques esos archivos.

## Pruebas y limitaciones

La actualización pasó 67 pruebas automáticas del escritorio, relacionadas con el conocimiento, las respuestas en ambos idiomas, los permisos, las consultas de registros y la persistencia de SQLite. Las pruebas de Gemini utilizan un proveedor simulado.

La cámara y la conexión real con Gemini deben comprobarse en Windows.

Esta actualización corresponde únicamente a la aplicación de escritorio. La versión web se actualiza y despliega por separado, y no puede consultar directamente la base de estudiantes almacenada en tu PC.
