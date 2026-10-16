# Preguntas que debes poder responder

| Pregunta | Respuesta sencilla |
| --- | --- |
| ¿Dónde está el LLM? | La API de Gemini genera la explicación después de recibir el contexto. El cliente está en `app/chatbot/llm.py` para escritorio y en `lib/assistant.mjs` para web. |
| ¿Qué parte es RAG? | Primero se recuperan fragmentos relevantes de la base; después se entregan al modelo para redactar la respuesta. La recuperación ocurre antes de la generación. |
| ¿Usaste embeddings? | No. Es recuperación léxica con coincidencias ponderadas y selección por número de principio. Es una decisión para un corpus pequeño y revisable; las paráfrasis complejas siguen siendo una limitación. |
| ¿Por qué no basta con SQLite? | SQLite almacena conocimiento, pero no es un modelo de lenguaje. La primera versión era un chatbot local de recuperación; la integración nueva añade la llamada al proveedor. |
| ¿Qué hace el system prompt? | Define propósito, límites, reglas de evidencia, comportamiento ético, ejemplos few-shot y formato de salida. No garantiza por sí solo que desaparezcan las alucinaciones. |
| ¿Cómo mantiene el contexto? | Conserva unos pocos turnos recientes y los artículos del tema anterior. El historial se trata como datos de baja confianza, no como instrucciones de sistema. |
| ¿Qué se valida en las citas? | Que los identificadores correspondan a documentos realmente recuperados. Esto evita referencias inventadas; no prueba que cada frase esté sustentada. |
| ¿Qué pasa si Gemini falla? | Se muestra un aviso y el contenido local de respaldo. La respuesta se identifica como local y no se cuenta como una respuesta del LLM. |
| ¿Por qué la clave está en el servidor? | Para que no viaje dentro del código que recibe el navegador y para no subirla a GitHub. |
| ¿El bot hace CRUD? | No. La guía permite un asistente en la interfaz y presenta el agente CRUD como una opción. Este diseño es educativo y de consulta; el LLM no modifica usuarios ni ingresos. |
| ¿Qué significa aumento humano aquí? | Ampliar la comprensión y las posibilidades de aprender, sin sustituir el juicio personal. Es una interpretación del proyecto; no se presenta como una definición literal de la Universidad. |
| ¿Qué relación tiene con PicMe? | Acompaña al proyecto de acceso facial con orientación educativa sobre MEDIT y la declaración. La base de conocimiento y el proveedor LLM están separados de los datos biométricos. |
| ¿Por qué no afirmas precisión del 100 %? | Porque las pruebas automáticas no equivalen a una evaluación completa con usuarios reales, y un LLM puede producir errores incluso con fuentes y restricciones. |
| ¿Qué falta para demostrar la entrega completa? | Verificar una llamada real con la clave, publicar GitHub, asegurar acceso del docente al despliegue y grabar el video en inglés. |
