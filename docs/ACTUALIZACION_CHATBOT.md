# Actualización del chatbot de escritorio

Esta actualización integra las consultas de registros y las respuestas en inglés del archivo `Cris_desktop.zip`, conservando la corrección anterior de la Declaración Persona Transhumana.

## Aplicarla en tu PC

1. Cierra PicMe.
2. Extrae `PicMe_Chatbot_Correcciones_Integradas.zip`.
3. Abre `Archivos_para_GitHub/desktop`. Copia su contenido dentro de la carpeta `desktop` del PicMe que ya funciona en tu PC y acepta reemplazar los archivos coincidentes. En tu instalación anterior esa carpeta era `C:\Users\yijan\Downloads\PicMe_Actividad_LLM\desktop`.
4. Dentro de esa carpeta ejecuta `ACTUALIZAR_BD.bat`. El resultado debe indicar **33 artículos y seis fuentes**.
5. Ejecuta `INICIAR_PICME.bat` y abre el chatbot.

El paquete contiene código, conocimiento y documentación. Tu archivo `.env`, el entorno instalado y los registros de estudiantes se conservan en el PC. La actualización de conocimiento usa `chatbot.db`; las consultas sobre estudiantes usan `picme.db` en modo de solo lectura.

Si necesitas ejecutarlo desde PowerShell, estando dentro de tu carpeta `desktop`:

```powershell
& ".\.venv\Scripts\python.exe" .\actualizar_conocimiento.py
& ".\.venv\Scripts\python.exe" .\run.py
```

## Preguntas para comprobarlo

| Pregunta | Qué debes observar |
| --- | --- |
| ¿Cuántas personas están registradas en PicMe? | Un conteo desde la base local y la etiqueta «Datos de PicMe · SQLite (solo lectura)». |
| How many people are registered in PicMe? | El mismo conteo, explicado en inglés. |
| ¿Cuál fue mi último ingreso? | Solicita iniciar sesión o consulta la cuenta de la sesión actual. |
| Explain principle 6 | Una explicación en inglés con su fuente institucional. |
| como se si soy una persona tras humana | Una reflexión educativa sobre la declaración, sin clasificar tu identidad. |

Las preguntas educativas usan Gemini cuando está configurado y disponible. Las consultas de registros se contestan localmente, incluso cuando Gemini está activado. La etiqueta SQLite en esas respuestas es el comportamiento esperado.

Para consultar el historial o la fecha de registro de otra persona, agrega en tu `.env` local:

```env
PICME_CHATBOT_ADMIN_EMAILS=correo_de_tu_cuenta_registrada
```

Después reinicia PicMe e inicia sesión con esa cuenta. Puedes autorizar varios correos separados por comas.

## Actualizar GitHub

Copia todo el contenido de `Archivos_para_GitHub` dentro de `C:\Users\yijan\Downloads\PicMe_GitHub`. Acepta reemplazar los archivos coincidentes. En PowerShell:

```powershell
cd "C:\Users\yijan\Downloads\PicMe_GitHub"
git add desktop README.md docs/ACTUALIZACION_CHATBOT.md
git commit -m "Integrar consultas de PicMe y respuestas bilingues"
git push origin main
```

Usa el paquete de actualización para subir el código. El ZIP original contiene también un archivo `.env`, bases locales, una clave de cifrado y el entorno `.venv`; esos archivos pertenecen a la instalación del PC.

## Alcance y verificación

Se aprobaron 67 pruebas automáticas del escritorio. Incluyen las consultas de reflexión anteriores, los doce principios en ambos idiomas, el acceso autorizado a historial, los conteos, los rechazos de escritura en SQLite y las pruebas de persistencia. Las pruebas del LLM usan un proveedor simulado.

La cámara y la conexión real de Gemini deben comprobarse en Windows. Esta actualización es del programa de escritorio. La versión web se actualiza y despliega por separado; sus visitantes no pueden consultar la base de estudiantes que está en tu PC.
