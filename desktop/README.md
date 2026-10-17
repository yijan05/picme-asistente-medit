# PicMe para Windows — escritorio, SQLite y Gemini

PicMe es un programa de escritorio con reconocimiento facial y un asistente educativo sobre UCundinamarca, el MEDIT y la Declaración Persona Transhumana.

## Abrir en Windows

1. Extrae todo el paquete. En la entrega completa, entra primero en la carpeta `desktop`.
2. Usa Python 3.10, 3.11 o 3.12 de 64 bits, con Tcl/Tk.
3. Abre `INSTALAR_WINDOWS.bat`. Crea un entorno `.venv`, instala las dependencias y descarga el modelo facial si falta. Necesita Internet la primera vez.
4. Para la actividad de Machine Learning, abre `CONFIGURAR_GEMINI.bat`, escribe la clave en `GEMINI_API_KEY` y guarda el archivo `.env` local.
5. Ejecuta `VERIFICAR_LLM.bat`. Solo confirma el LLM cuando recibe una respuesta real del proveedor; una respuesta local no pasa esa verificación.
6. Abre `INICIAR_PICME.bat` o `SOLO_CHATBOT.bat`.

El chat también funciona sin clave, en modo local. Ese modo permite consultar el conocimiento, pero por sí solo no cumple el requisito de LLM de la actividad.

## Configuración del LLM

`.env.example` contiene los nombres de las variables, sin una clave real:

```text
GEMINI_API_KEY=
GEMINI_MODEL=gemini-3.5-flash-lite
PICME_CHAT_MODE=auto
```

`auto` utiliza Gemini si hay clave. `local` permite elegir la consulta local aunque exista una clave. Al activar Gemini, se envían la pregunta y los fragmentos recuperados al proveedor; la base biométrica no se envía.

`app/chatbot/rag.py` recupera hasta cuatro artículos y prepara el historial. `app/chatbot/llm.py` construye una petición REST con system prompt, contexto y salida JSON. Los enlaces se construyen a partir de referencias que pertenecen a los documentos recuperados. La interfaz distingue la respuesta de Gemini, la consulta local y el respaldo ante un error del proveedor.

El prompt está en `conocimiento/system_prompt.txt`. Contiene propósito, restricción de dominio, reglas de evidencia, ejemplos few-shot y relación con los principios transhumanos. Se usa recuperación léxica, no embeddings.

Las consultas de reflexión personal, por ejemplo «como se si soy una persona tras humana», recuperan una actividad didáctica y los doce compromisos completos. El asistente reconoce la palabra separada y variantes comunes; ayuda a reflexionar sin asignar identidades ni emitir certificaciones. El prompt también pide revisar ortografía y concordancia.

## Bases de datos

| Archivo | Contenido |
| --- | --- |
| `data/picme.db` | Usuarios, rutas biométricas y accesos locales. |
| `data/chatbot.db` | 33 artículos y seis fuentes del asistente. |
| `conocimiento/base_conocimiento.json` | Fuente editable para importar el conocimiento. |
| `app/chatbot/schema.sql` | Esquema SQLite del chatbot. |

Ambas bases se crean automáticamente si faltan. La fuente preparada para GitHub excluye registros de personas, claves y plantillas biométricas. Si usas el paquete anterior con datos, conserva `data` y la clave de cifrado para mantenerlos. Los registros nuevos guardan rutas relativas y se pueden resolver rutas antiguas hacia otro PC.

Para cambiar el contenido, edita `conocimiento/base_conocimiento.json`, ejecuta `ACTUALIZAR_BD.bat` y vuelve a abrir el chat. El importador valida antes de modificar y revierte la transacción ante errores. Las conversaciones permanecen en memoria y no se guardan en SQLite.

## Preguntas para probar

- ¿Qué es el MEDIT?
- ¿Cuáles son las dimensiones del MEDIT?
- Muéstrame los doce principios.
- Explícame el principio 6 con un ejemplo para trabajar en equipo.
- Compara los principios 5 y 9. La explicación comparativa se solicita al LLM si está configurado.
- ¿Qué significa me valoro y cuido?
- ¿Dónde queda la universidad en Ubaté?

Después de un principio, prueba `y el siguiente` o `dame un ejemplo`. La respuesta muestra su fuente. El LLM puede equivocarse: contrasta lo que afirma.

## Comandos equivalentes

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run.py
```

```powershell
py -3.10 run.py --chatbot
py -3.10 chatbot.py "Explícame el principio 6"
py -3.10 verificar_llm.py
```

## Diagnóstico

Ejecuta `DIAGNOSTICAR_WINDOWS.bat` si la ventana no abre. Para comprobar también el modelo y la cámara:

```powershell
.\.venv\Scripts\python.exe diagnosticar.py --modelo --camara
```

Cierra otras aplicaciones que estén usando la cámara y revisa los permisos de Windows. Para otra cámara, configura `PICME_CAMERA_INDEX=1` en el entorno antes de abrir el programa.

Si un registro antiguo usa una versión distinta de scikit-learn, puede aparecer un aviso de compatibilidad. Los registros nuevos se entrenan con las versiones de este paquete; la lectura del modelo antiguo no demuestra su precisión con una cámara real.

## Verificación

Esta actualización pasó 67 pruebas del conocimiento, RAG, respuestas bilingües, consultas de registros, permisos y SQLite. Las pruebas del proveedor usan respuestas simuladas. `VERIFICAR_LLM.bat` permite comprobar una llamada real desde tu PC. La cámara física debe probarse allí.

```powershell
.\.venv\Scripts\python.exe pruebas_locales.py
```

Para las pruebas del backend MySQL opcional, instala `requirements-backend.txt` y añade `--backend`. MySQL y FastAPI no son necesarios para el programa de escritorio.

La entrega completa incluye la web, reflexión en español e inglés, guion del video y guía de publicación en el README principal y `docs/`.


## Consultas de registros e idiomas

El chat de escritorio también responde en inglés. Las traducciones para la consulta local están en `conocimiento/traducciones_en.json`. Las consultas sobre registros e ingresos se resuelven con `app/chatbot/picme_queries.py`, usando SQLite de solo lectura.

Puedes preguntar «¿Cuántas personas están registradas en PicMe?» o «How many people are registered in PicMe?». Para «¿Cuál fue mi último ingreso?» debes iniciar sesión. Para consultar datos de otras personas, inicia sesión con una cuenta cuyo correo figure en `PICME_CHATBOT_ADMIN_EMAILS`, en el archivo `.env` local. Se permiten varios correos separados por comas.

Los resultados de las consultas de registros no se envían a Gemini. El módulo no crea, modifica ni elimina cuentas, y no consulta hashes de contraseñas ni plantillas faciales.
