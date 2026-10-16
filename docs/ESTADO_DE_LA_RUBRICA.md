# Estado verificable de la entrega

Esta tabla distingue implementación de evidencia. No estima una calificación ni presenta pruebas simuladas como llamadas reales.

| Criterio | Implementado | Evidencia o paso pendiente |
| --- | --- | --- |
| LLM e integración, 25 % | Gemini REST, interfaces de escritorio y web, contexto acotado, manejo de errores y respuesta estructurada. | Configurar una clave y verificar una respuesta real del proveedor. Los contratos HTTP se probaron con respuestas simuladas. |
| Conocimiento y prompting, 20 % | 32 artículos, 6 fuentes, SQLite en escritorio, RAG léxico, system prompt, few-shot, dominio y referencias validadas. | Evaluar exactitud con preguntas reales al modelo; la validación de referencias no demuestra ausencia de alucinaciones. |
| Cloud y GitHub, 15 % | Código preparado para alojamiento web y publicación; fuentes sin claves ni datos biométricos. | Permitir acceso al docente al sitio publicado y publicar el repositorio en GitHub. El enlace de alojamiento se confirma al finalizar la entrega. El acceso inicial del sitio es privado. |
| Declaración ES/EN, 20 % | Reflexión crítica en ambos idiomas en README e interfaz. Relación con decisiones reales de diseño. | Revisar el texto y adaptarlo a tu manera de explicarlo. |
| Video en inglés, 20 % | Guion y secuencia de demostración para menos de cinco minutos. | Grabar tu sustentación y adjuntar el enlace del video. |

## Qué se comprobó

- Las pruebas de la base y del contrato de Gemini usan datos controlados y proveedores simulados.
- La integración distingue `llmUsed: true` / `llm_usado: true` de la consulta local y del respaldo.
- La clave no está configurada en el entorno de construcción. No se realizó una llamada real autenticada a Gemini durante esta preparación.
- El paquete original contenía datos y plantillas biométricas de prueba. Se excluyen de la fuente preparada para publicar; el programa puede crear una base nueva y registrar usuarios localmente.

Los resultados concretos de pruebas y publicación se registran en `VERIFICACION.md`.
