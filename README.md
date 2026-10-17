# PicMe

Proyecto de la Universidad de Cundinamarca para la materia de Introducción a Machine Learning.

PicMe es una aplicación de escritorio que permite registrar estudiantes y controlar su ingreso mediante reconocimiento facial. También tiene un chatbot que responde preguntas sobre la universidad, el MEDIT y los 12 principios de la Declaración Persona Transhumana.

Además, el chatbot se puede usar desde una página web.

**Repositorio:** [picme-asistente-medit](https://github.com/yijan05/picme-asistente-medit)

## Lo que hace el chatbot

- Registrar estudiantes y controlar sus ingresos con reconocimiento facial.
- Consultar el historial de ingresos y algunas estadísticas de PicMe.
- Responder preguntas sobre el MEDIT y la Declaración Persona Transhumana.
- Contestar en español e inglés.
- Usar Gemini para generar respuestas basadas en los documentos del proyecto.
- Mostrar las fuentes utilizadas para responder.

El chatbot también puede consultar su propia base de conocimiento cuando Gemini no está disponible.

## Funcionaminento

El chatbot busca los documentos relacionados con la pregunta y utiliza la información encontrada para preparar una respuesta con Gemini. Esta técnica se conoce como **RAG**.

La base de conocimiento contiene 33 artículos y seis fuentes institucionales. No se entrenó un modelo de inteligencia artificial desde cero; se integró la API de Gemini con la información recopilada para el proyecto.

## Instalación en Windows

Necesitas Python de 64 bits, versión 3.10, 3.11 o 3.12, y conexión a Internet para instalar las dependencias.

1. Entra a la carpeta `desktop`.
2. Ejecuta `INSTALAR_WINDOWS.bat`.
3. Ejecuta `CONFIGURAR_GEMINI.bat` y configura tu clave en el archivo `.env`:

   ```env
   GEMINI_API_KEY=tu_clave
   GEMINI_MODEL=gemini-3.8-flash
   PICME_CHAT_MODE=auto
   ```

   Puedes conseguir una clave en [Google AI Studio](https://aistudio.google.com/apikey).

4. Ejecuta `VERIFICAR_LLM.bat` para comprobar la conexión.
5. Abre PicMe con `INICIAR_PICME.bat` o ejecuta `SOLO_CHATBOT.bat` para abrir únicamente el chatbot.

**Nota:** si no configuras Gemini, el chatbot puede seguir respondiendo con la información local. No subas tu archivo `.env` ni tu clave a GitHub.

## Version web

Para ejecutar la página en desarrollo, necesitas Node.js 22.13 o posterior y pnpm.

Desde la carpeta raíz del proyecto, ejecuta:

```bash
pnpm install --frozen-lockfile
pnpm dev
```

Para publicar la página en Vercel, sigue la [guía de despliegue](docs/DESPLEGAR_EN_VERCEL.md).

Recuerda configurar `GEMINI_API_KEY` y `GEMINI_MODEL` en las variables de entorno de Vercel. El archivo `.env` de tu computador no configura automáticamente la versión publicada.

## Organización del proyecto

| Carpeta o archivo | ¿Para qué sirve? |
|---|---|
| `desktop/` | Aplicación de escritorio. |
| `desktop/app/chatbot/` | Lógica del chatbot, búsqueda de información y conexión con Gemini. |
| `desktop/conocimiento/` | Artículos, traducciones e instrucciones del asistente. |
| `desktop/data/` | Bases de datos SQLite de PicMe y del chatbot. |
| `app/` | Interfaz y servicio del chatbot web. |
| `lib/` | Lógica, información e instrucciones del chatbot web. |

## Bases de datos

PicMe utiliza dos bases de datos:

- `desktop/data/picme.db`: guarda los usuarios, las referencias a las plantillas faciales y el historial de ingresos.
- `desktop/data/chatbot.db`: guarda los artículos, las fuentes y otros datos del chatbot.

Las plantillas faciales se almacenan cifradas en archivos externos. Las consultas estadísticas del chatbot son de solo lectura y el acceso a los datos depende de los permisos de cada usuario.

## Documentación

- [Guía para actualizar el chatbot](docs/ACTUALIZACION_CHATBOT.md)
- [Pruebas realizadas](docs/VERIFICACION.md)
- [Guion del video en inglés](docs/VIDEO_SCRIPT_EN.md)
- [Guía para grabar el video](docs/GUIA_GRABACION_ES.md)
- [Estado de la rúbrica](docs/ESTADO_DE_LA_RUBRICA.md)

## Fuentes consultadas

- [Declaración Persona Transhumana](https://www.ucundinamarca.edu.co/index.php/noticias-ucundinamarca/120-rectoria/3816-declaracionpersonatranshumana)
- [Modelo Educativo Digital Transmoderno (MEDIT)](https://www.ucundinamarca.edu.co/index.php/modelo-educativo-digital-transmoderno)
- [Ejes del MEDIT](https://www.ucundinamarca.edu.co/index.php/noticias-ucundinamarca/112-institucional/medit/3947-el-sosten-del-modelo-educativo)
- [Universidad de Cundinamarca — Seccional Ubaté](https://www.ucundinamarca.edu.co/index.php/sedes/Seccionalubate)
- [Documentación de Gemini](https://ai.google.dev/gemini-api/docs)

---

*Proyecto académico desarrollado para la Universidad de Cundinamarca.*
