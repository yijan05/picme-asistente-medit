# Pruebas realizadas

| Prueba | Resultado | Observación |
| --- | --- | --- |
| Instalación en Windows | Completada | Se instalaron las dependencias y se descargó el modelo facial. |
| Conexión real a Gemini | Correcta | El diagnóstico devolvió HTTP 200, modo gemini y modelo gemini-3.5-flash-lite. |
| Consulta desde PicMe | Correcta | Se explicó el principio 6 y se respondió la consulta de reflexión personal con una fuente. |
| Pregunta «como se si soy una persona tras humana» | Corregida | Se reconocen variantes de escritura y se recupera el contexto de la declaración. |
| Buscador y RAG en Python | 43 pruebas aprobadas | Incluyen límites, preguntas fuera del tema, recuperación, referencias y respaldo ante errores. El proveedor se simula en las pruebas automáticas. |
| Lógica del chatbot web | 13 pruebas aprobadas | Incluyen recuperación, seguimiento, transporte, formato y errores del proveedor. |
| Instalador de la corrección | Comprobado | Conserva la configuración, los registros y los artículos propios. Se probó la restauración del respaldo ante un fallo. |
| Repositorio público | Disponible | https://github.com/yijan05/picme-asistente-medit |
| Gemini y acceso del docente en la web | Pendientes | El servidor todavía requiere su configuración de Gemini y acceso para la evaluación. |
| Cámara y reconocimiento facial con personas | Por evaluar en el equipo | La instalación de las dependencias no demuestra la precisión del reconocimiento. |
| Video en inglés | Pendiente | Debe durar como máximo cinco minutos y mostrar el funcionamiento y el código. |

Recuperar un documento relacionado y comprobar su referencia ayuda a revisar las respuestas, pero no garantiza que cada afirmación del modelo sea correcta. También deben contrastarse el contenido, los ejemplos y la redacción.
