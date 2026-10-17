# PicMe

Sistema académico de control de ingreso mediante reconocimiento facial, desarrollado para la Universidad de Cundinamarca. Integra una aplicación de escritorio y una versión web con un chatbot educativo sobre el Modelo Educativo Digital Transmoderno (MEDIT) y los doce principios de la Declaración Persona Transhumana.

**Repositorio:** https://github.com/yijan05/picme-asistente-medit

## Funcionalidades

### Aplicación de escritorio
- Registro de estudiantes y control de ingreso mediante reconocimiento facial.
- Gestión local de usuarios e historial de ingresos con SQLite.
- Chatbot bilingüe (español e inglés).
- Consultas de solo lectura sobre estadísticas de registros e ingresos, sujetas a permisos.

### Chatbot educativo
- Responde preguntas sobre el MEDIT, la Declaración Persona Transhumana y la Universidad de Cundinamarca.
- Consulta una base de conocimiento con 33 artículos y seis fuentes institucionales.
- Utiliza Gemini para generar respuestas a partir de documentos recuperados.
- Muestra las fuentes consultadas y distingue las respuestas de Gemini de las respuestas locales.
- Mantiene un historial breve para comprender preguntas de seguimiento.

El chatbot utiliza **RAG (Retrieval-Augmented Generation)**: busca documentos mediante coincidencias entre la pregunta, los títulos, las palabras clave y las preguntas de ejemplo; después, proporciona hasta cuatro artículos como contexto para Gemini. El proyecto no entrena un modelo propio ni utiliza embeddings.

## Requisitos

- **Escritorio:** Windows y Python de 64 bits, versión 3.10, 3.11 o 3.12.
- **Web:** Node.js 22.13 o posterior y pnpm.
- Conexión a Internet para instalar dependencias y utilizar la API de Gemini.

## Instalación en Windows

1. Abre la carpeta `desktop`.
2. Ejecuta `INSTALAR_WINDOWS.bat`.
3. Ejecuta `CONFIGURAR_GEMINI.bat` y configura las variables en el archivo `.env`:

   ```env
   GEMINI_API_KEY=tu_clave_de_gemini
   GEMINI_MODEL=gemini-3.8-flash
   PICME_CHAT_MODE=auto
   ```

   Obtén tu clave en [Google AI Studio](https://aistudio.google.com/apikey).

4. Ejecuta `VERIFICAR_LLM.bat` para comprobar la conexión.
5. Inicia PicMe con `INICIAR_PICME.bat` o abre únicamente el chatbot con `SOLO_CHATBOT.bat`.

Si no configuras una clave de Gemini, el chatbot puede utilizar la base de conocimiento local. Si la API no está disponible, la aplicación puede mostrar una respuesta de respaldo.

**Importante:** no publiques el archivo `.env` ni incluyas tu clave de API en el repositorio.

## Ejecutar y desplegar la versión web

Desde la raíz del proyecto, instala las dependencias e inicia el entorno de desarrollo:

```bash
pnpm install --frozen-lockfile
pnpm dev
```

Para desplegar la aplicación en Vercel, consulta la [guía de despliegue](docs/DESPLEGAR_EN_VERCEL.md).

Configura `GEMINI_API_KEY` y `GEMINI_MODEL` en **Settings → Environment Variables** del proyecto en Vercel. El archivo `.env` de tu computador no configura las variables del servidor desplegado.

## Estructura del proyecto

| Ruta | Descripción |
|---|---|
| `desktop/app/chatbot/engine.py` | Búsqueda local de contenido relacionado con la pregunta. |
| `desktop/app/chatbot/rag.py` | Recuperación de documentos y preparación del contexto. |
| `desktop/app/chatbot/llm.py` | Integración con Gemini y validación de respuestas. |
| `desktop/app/chatbot/picme_queries.py` | Consultas autorizadas de estadísticas e historial. |
| `desktop/app/db.py` | Gestión de usuarios, plantillas e ingresos. |
| `desktop/conocimiento/base_conocimiento.json` | Artículos y fuentes del chatbot de escritorio. |
| `desktop/conocimiento/traducciones_en.json` | Traducciones al inglés para las consultas locales. |
| `desktop/conocimiento/system_prompt.txt` | Reglas y ejemplos del asistente de escritorio. |
| `app/page.tsx` | Interfaz web. |
| `app/api/chat/route.ts` | Endpoint del chatbot web. |
| `lib/assistant.mjs` | Lógica de búsqueda y respuesta de la versión web. |
| `lib/knowledge.json` | Base de conocimiento web. |
| `lib/prompt.mjs` | Instrucciones del asistente web. |

## Bases de datos y privacidad

PicMe utiliza dos bases de datos SQLite:

| Base de datos | Contenido |
|---|---|
| `desktop/data/picme.db` | Usuarios, referencias a plantillas faciales e historial de ingresos. |
| `desktop/data/chatbot.db` | Artículos, fuentes, preguntas de ejemplo y metadatos del conocimiento. |

Las bases se crean al iniciar la aplicación si no existen. El repositorio no incluye estudiantes registrados. Las plantillas faciales se almacenan cifradas en archivos externos y la base de datos conserva sus rutas.

Las consultas estadísticas son de solo lectura. Consultar la fecha de registro y el último ingreso propios requiere iniciar sesión; acceder a los datos de otras personas requiere autorización mediante `PICME_CHATBOT_ADMIN_EMAILS`.

Los resultados de estas consultas no se incorporan al historial enviado a Gemini. El chatbot no crea, modifica ni elimina estudiantes.

Para actualizar la base de conocimiento del escritorio, modifica los archivos JSON correspondientes y ejecuta `ACTUALIZAR_BD.bat`.

## Pruebas y limitaciones

- Se realizaron pruebas del chatbot sobre el MEDIT y la Declaración Persona Transhumana.
- Las pruebas automatizadas del escritorio cubren recuperación de conocimiento, respuestas bilingües, permisos y consultas SQLite.
- Las pruebas con respuestas simuladas no sustituyen la comprobación real de la API.
- El reconocimiento facial debe evaluarse con la cámara y el dispositivo reales.
- Las respuestas del chatbot requieren revisión humana, ya que pueden contener errores.

Consulta la [guía de actualización del chatbot](docs/ACTUALIZACION_CHATBOT.md) y la [documentación de verificación](docs/VERIFICACION.md) para más detalles.

## Material de apoyo

- [Guion del video en inglés](docs/VIDEO_SCRIPT_EN.md)
- [Guía de grabación](docs/GUIA_GRABACION_ES.md)
- [Estado de la rúbrica](docs/ESTADO_DE_LA_RUBRICA.md)

## Fuentes institucionales

- [Declaración Persona Transhumana](https://www.ucundinamarca.edu.co/index.php/noticias-ucundinamarca/120-rectoria/3816-declaracionpersonatranshumana)
- [Modelo Educativo Digital Transmoderno (MEDIT)](https://www.ucundinamarca.edu.co/index.php/modelo-educativo-digital-transmoderno)
- [Ejes del modelo educativo](https://www.ucundinamarca.edu.co/index.php/noticias-ucundinamarca/112-institucional/medit/3947-el-sosten-del-modelo-educativo)
- [Seccional Ubaté](https://www.ucundinamarca.edu.co/index.php/sedes/Seccionalubate)
- [Libro MEDIT](https://www.ucundinamarca.edu.co/index.php/rectoria/libro-medit)
- [Plan de Desarrollo 2024–2027](https://www.ucundinamarca.edu.co/documents/secretaria-general/PLAN%20DE%20DESARROLLO%202024-2027.pdf)
- [Documentación de Gemini API](https://ai.google.dev/gemini-api/docs)

---

*PicMe es un proyecto académico. Para trámites e información institucional vigente, consulta los canales oficiales de la Universidad de Cundinamarca.*
