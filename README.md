# PicMe

Universidad de Cundinamarca, seccional Ubaté  
Ingeniería de Sistemas y Computación  
CADI: Introducción a Machine Learning  
Evelin Yijan Virguez Parra

PicMe es un proyecto de control de ingreso mediante reconocimiento facial. Para esta actividad se integró un chatbot que responde preguntas sobre la Universidad de Cundinamarca, el MEDIT y los doce principios de la Declaración Persona Transhumana.

El chatbot se puede abrir desde PicMe o de forma independiente. También existe una versión web para consultar los contenidos educativos. Los registros de estudiantes se manejan en la aplicación de escritorio.

Repositorio: https://github.com/yijan05/picme-asistente-medit

## Qué hace el chatbot

- Explica el MEDIT y los principios de la declaración con ejemplos.
- Consulta una base de conocimiento con 33 artículos y seis fuentes institucionales.
- Usa Gemini para redactar la respuesta a partir de los documentos recuperados.
- Muestra la fuente de la información y señala si respondió Gemini o la consulta local.
- Conserva un historial breve para entender preguntas de seguimiento.
- En el escritorio responde en español o inglés y consulta estadísticas de registros e ingresos mediante SQLite, con consultas de solo lectura.

Por ejemplo, se puede preguntar «Explícame el principio 6», «¿Cuáles son los ejes del MEDIT?» o «¿Cómo sé si soy una persona transhumana?». En esta última pregunta propone una reflexión sobre las acciones cotidianas, sin decidir la identidad de quien consulta.

## Cómo ejecutarlo en Windows

Se necesita Python 3.10, 3.11 o 3.12 de 64 bits. La instalación requiere conexión a Internet.

1. Abre la carpeta `desktop` y ejecuta `INSTALAR_WINDOWS.bat`.
2. Ejecuta `CONFIGURAR_GEMINI.bat`. Guarda tu clave en el archivo `.env` y configura el modelo:

   ```env
   GEMINI_API_KEY=tu_clave_local
   GEMINI_MODEL=gemini-3.5-flash-lite
   PICME_CHAT_MODE=auto
   ```

3. Ejecuta `VERIFICAR_LLM.bat` para comprobar la conexión.
4. Abre `INICIAR_PICME.bat` para entrar a PicMe o `SOLO_CHATBOT.bat` para abrir el asistente.

Si el lanzador de Python falla, ejecuta el instalador desde PowerShell con la ruta de tu instalación. En el equipo usado para el proyecto se empleó:

```powershell
& "C:\Program Files\Python310\python.exe" .\instalar_windows.py
```

El archivo `.env` se conserva en el equipo y queda excluido de Git. Sin clave, el chatbot permite consultar la base local. Cuando falla Gemini, la interfaz indica que se está mostrando una respuesta de respaldo.

## Cómo está organizado

| Archivo o carpeta | Función |
| --- | --- |
| `desktop/app/chatbot/engine.py` | Busca el contenido relacionado con la pregunta y reconoce variantes de escritura. |
| `desktop/app/chatbot/rag.py` | Selecciona los documentos y prepara el contexto de la conversación. |
| `desktop/app/chatbot/llm.py` | Envía la solicitud a Gemini y revisa el formato de la respuesta. |
| `desktop/app/chatbot/picme_queries.py` | Consulta estadísticas e historial autorizado de PicMe en SQLite. |
| `desktop/conocimiento/traducciones_en.json` | Contiene las traducciones de los 33 artículos para la consulta local en inglés. |
| `desktop/conocimiento/base_conocimiento.json` | Contiene los artículos y sus fuentes. |
| `desktop/conocimiento/system_prompt.txt` | Define el propósito, las reglas y los ejemplos del asistente. |
| `desktop/app/db.py` | Maneja usuarios, plantillas e ingresos en SQLite. |
| `app/page.tsx` y `app/api/chat/route.ts` | Interfaz y servicio del chatbot web. |
| `lib/assistant.mjs`, `lib/knowledge.json` y `lib/prompt.mjs` | Búsqueda, conocimiento y prompt de la versión web. |

La recuperación es léxica: compara las palabras de la pregunta con los títulos, las palabras clave y las preguntas de ejemplo. Luego envía hasta cuatro artículos a Gemini. A esta combinación de recuperación y generación se le llama RAG. No se entrenó un modelo propio ni se utilizaron embeddings.

El system prompt limita las respuestas al tema del proyecto, separa los documentos de las instrucciones y pide identificar los artículos utilizados. Incluye ejemplos de respuesta, también llamados few-shot. El programa comprueba esos identificadores y agrega los enlaces desde su catálogo de fuentes.

## Bases de datos

| Base | Contenido |
| --- | --- |
| `desktop/data/picme.db` | Usuarios, referencias a sus plantillas faciales e historial de ingresos. |
| `desktop/data/chatbot.db` | Fuentes, artículos, preguntas de ejemplo y metadatos del conocimiento. |

Ambas bases se crean al iniciar la aplicación si aún no existen. El código publicado comienza sin estudiantes registrados. Las plantillas faciales se guardan cifradas en archivos externos; la base conserva sus rutas.

Para actualizar el conocimiento, se edita el JSON y se ejecuta `ACTUALIZAR_BD.bat`. Las preguntas sobre estadísticas de registros e ingresos se atienden en el escritorio con consultas SQLite de solo lectura. La fecha de registro y el último ingreso propios requieren iniciar sesión; los datos de otras personas requieren una cuenta autorizada mediante `PICME_CHATBOT_ADMIN_EMAILS`. Los resultados de estas consultas no se incorporan al historial enviado a Gemini. El chat no crea, modifica ni elimina estudiantes.

Consulta la [guía de esta actualización](docs/ACTUALIZACION_CHATBOT.md) para aplicar los cambios y probarlos.

## Versión web y entrega

La web utiliza React y TypeScript. Incluye configuración para Vercel con Next.js y para Cloudflare Workers con Vinext. Para ejecutarla en desarrollo se necesita Node.js 22.13 o posterior:

```bash
npx pnpm install --frozen-lockfile
npx pnpm dev
```

Para publicarla en Vercel, sigue la [guía de despliegue](docs/DESPLEGAR_EN_VERCEL.md). Las variables `GEMINI_API_KEY` y `GEMINI_MODEL` se configuran en el panel del alojamiento. El archivo `.env` del PC no configura ese servidor.

El repositorio público y la conexión de Gemini en Windows ya funcionan. Para terminar la entrega falta habilitar el acceso al sitio para su evaluación, configurar y comprobar Gemini en la web y grabar el video en inglés de máximo cinco minutos.

El video puede mostrar la interfaz de PicMe en el PC. También debe explicar la arquitectura, la conexión a la API, el prompt y la base de conocimiento. La guía solicita además un enlace funcional a la aplicación desplegada en la nube.

- [Guion de apoyo en inglés](docs/VIDEO_SCRIPT_EN.md).
- [Guía de grabación](docs/GUIA_GRABACION_ES.md).
- [Estado de la entrega](docs/ESTADO_DE_LA_RUBRICA.md).
- [Pruebas realizadas](docs/VERIFICACION.md).

## Reflexión en español

**¿De qué manera el chatbot respeta y fomenta los principios de la Declaración Persona Transhumana en el aprendizaje y la interacción tecnológica?**

En PicMe, el chatbot sirve para comprender los principios y relacionarlos con situaciones cotidianas. Los principios 1, 4, 9 y 10 hablan de dirigir la propia vida, aprender, formar el carácter y asumir responsabilidades. Por eso, el asistente propone preguntas y ejemplos que el estudiante puede analizar. La decisión y la reflexión siguen siendo de la persona.

El cuidado de la vida y del bienestar, presente en los principios 2, 3, 5 y 12, también orienta el proyecto. Una respuesta debe ser comprensible y respetuosa. El chat educativo trabaja con documentos institucionales y no necesita consultar fotografías, plantillas faciales o contraseñas de los estudiantes. Al usar Gemini, la pregunta y los fragmentos de contexto se envían al proveedor; por eso se informa el modo utilizado y también existe una consulta local.

El principio 6 invita a considerar a los demás, los seres vivos y la naturaleza. Aplicarlo al proyecto implica pensar en las consecuencias de nuestras decisiones técnicas. Por ejemplo, una dificultad del reconocimiento facial no debe llevar a tratar de manera injusta a un estudiante. El chatbot tampoco debe poner etiquetas sobre la identidad de una persona. El principio 8 se relaciona con mantener un diálogo respetuoso y apoyar la convivencia.

Los principios 7 y 11 recuerdan que mejorar requiere responsabilidad y que el desarrollo personal no depende necesariamente de la tecnología. Integrar Gemini puede facilitar una explicación, pero eso no significa que todas sus respuestas sean correctas. Por esta razón se muestran fuentes y se revisa qué documentos se recuperaron. Aun así, los errores de interpretación y de redacción requieren revisión humana.

La transformación educativa se evidencia cuando la herramienta ayuda a comprender y a tomar mejores decisiones. Para evaluarla hace falta probar preguntas reales, revisar errores y escuchar a quienes la utilizan. Tener una API conectada es una parte del proyecto; su utilidad para aprender debe comprobarse.

## Reflection in English

**How does the chatbot support the Transhuman Person Declaration regarding ethical AI integration, human augmentation and educational transformation?**

In PicMe, the chatbot helps students understand the declaration and connect its principles with everyday situations. Principles 1, 4, 9 and 10 address autonomy, learning, character and responsibility. The assistant therefore offers questions and examples for the student to consider. The learner remains responsible for their own decisions and reflection.

Care for life and well-being, expressed in principles 2, 3, 5 and 12, also guides the project. Responses should be clear and respectful. The educational chat uses institutional documents and does not need students' photographs, facial templates or passwords. When Gemini is enabled, the question and the retrieved passages are sent to the provider. The interface identifies the response mode, and a local knowledge lookup is also available.

Principle 6 asks us to consider other people, living beings and nature. In this project, this means considering the consequences of technical decisions. For example, a facial recognition problem should not lead to unfair treatment of a student. The chatbot should not assign identities to people either. Principle 8 supports respectful dialogue and peaceful coexistence.

Principles 7 and 11 connect improvement with responsibility and remind us that personal development does not necessarily depend on technology. Gemini can help explain a topic, but this does not make every answer correct. The application shows sources and checks the document references. Interpretation and writing errors still require human review.

Educational transformation depends on whether the tool helps people understand and make better-informed decisions. This requires real questions, error review and feedback from users. Connecting an API is one part of the project; its educational value must also be evaluated.

## Pruebas

En Windows se comprobó una respuesta real con HTTP 200 y el modelo `gemini-3.5-flash-lite`. Después se probaron preguntas sobre la declaración en la interfaz de PicMe.

La actualización del escritorio pasó 67 pruebas sobre conocimiento, RAG, respuestas bilingües, consultas de registros, permisos y persistencia SQLite. Las 13 pruebas web se habían completado en la versión anterior. Las pruebas automáticas del proveedor usan respuestas simuladas; esta actualización del escritorio no modifica la web. La evaluación de la cámara y de la precisión del reconocimiento facial requiere pruebas con personas y con el dispositivo real.

## Fuentes principales

- [Declaración Persona Transhumana](https://www.ucundinamarca.edu.co/index.php/noticias-ucundinamarca/120-rectoria/3816-declaracionpersonatranshumana).
- [Modelo Educativo Digital Transmoderno](https://www.ucundinamarca.edu.co/index.php/modelo-educativo-digital-transmoderno).
- [Los ejes del modelo educativo](https://www.ucundinamarca.edu.co/index.php/noticias-ucundinamarca/112-institucional/medit/3947-el-sosten-del-modelo-educativo).
- [Seccional Ubaté](https://www.ucundinamarca.edu.co/index.php/sedes/Seccionalubate).
- [Libro MEDIT](https://www.ucundinamarca.edu.co/index.php/rectoria/libro-medit).
- [Plan de Desarrollo 2024–2027](https://www.ucundinamarca.edu.co/documents/secretaria-general/PLAN%20DE%20DESARROLLO%202024-2027.pdf), página 17.
- [Documentación de Gemini](https://ai.google.dev/gemini-api/docs).

PicMe es un proyecto académico. Para trámites e información institucional vigente se deben consultar los canales oficiales de la Universidad.

