# Cómo preparar el video

El video debe mostrar tu pantalla y tu explicación en inglés. El guion está en `VIDEO_SCRIPT_EN.md`; no está grabado todavía.

Antes de grabar:

1. Configura la clave real de Gemini en el entorno del servidor o en `desktop/.env` para la versión de escritorio.
2. En escritorio, ejecuta `VERIFICAR_LLM.bat`. Debe decir **VERIFICADO** y mostrar `Modo: gemini`. Una respuesta local no acredita la API.
3. Para la demostración web, realiza una pregunta y comprueba que esa respuesta lleva la etiqueta **Gemini**. El indicador “configurado” por sí solo no demuestra una llamada exitosa.
4. Publica el repositorio y verifica que tu docente puede abrir tanto GitHub como la aplicación. El sitio de esta entrega empieza con acceso privado.
5. Abre el proyecto en VS Code, el navegador con la aplicación y la fuente oficial.

| Tiempo aproximado | Qué muestras |
| --- | --- |
| 0:00–0:25 | Nombre del proyecto y propósito. |
| 0:25–1:10 | `app/page.tsx`, `app/api/chat/route.ts`, `lib/assistant.mjs`. |
| 1:10–2:00 | `lib/knowledge.json`, `lib/prompt.mjs` y validación de referencias. |
| 2:00–3:10 | Una consulta real a Gemini y una consulta sin evidencia. |
| 3:10–4:00 | Reflexión bilingüe y decisiones éticas. |
| 4:00–4:25 | Repositorio público, sitio accesible y cierre. |

Preguntas sugeridas para la demostración:

- `Compara los principios 5 y 9 en el contexto del aprendizaje.`
- `¿Cuál es la capital de Perú?` Esta base no contiene esa información y debe reconocer el límite.

Ensaya con cronómetro. El objetivo es terminar alrededor de 4:25 y reservar tiempo para la respuesta del proveedor. No muestres la clave, el contenido de `.env` ni los registros biométricos.

La nota sobre asistencia presencial de la guía es un requisito independiente: el código y el video no permiten acreditar esa asistencia.
