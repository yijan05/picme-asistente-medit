# Registro de verificación

Preparación: 15 de octubre de 2026, hora de Colombia.

| Verificación | Resultado | Alcance |
| --- | --- | --- |
| Pruebas Python completas | 192 aprobadas | Linux, Python 3.12; flujos locales y contratos del proveedor con simulaciones. |
| Contrato y RAG Python después del ajuste final | 13 aprobadas | Peticiones REST, contexto, JSON, citas y errores de proveedor simulados. |
| Pruebas web | 12 aprobadas | Recuperación, comparación, seguimiento, límites, formato de petición y respuestas HTTP simuladas. |
| Ventana Tkinter con RAG | Correcta | Consulta en hilo, recepción en Tk, etiqueta de modo, limpieza y cierre; proveedor simulado. |
| TypeScript | Sin errores | `tsc --noEmit`. |
| Compilación web | Correcta | Frontend, endpoint de chat y endpoint de estado. |
| Sintaxis de escritorio | Compatible con Python 3.10 | Análisis sintáctico; no ejecución nativa de Windows. |
| Fuente para publicar | Sin bases biométricas ni claves | Se excluyeron registros de usuarios, plantillas, modelos de usuarios y archivos de credenciales. |
| LLM autenticado real | Pendiente | No había una clave de Gemini configurada. Ejecutar `VERIFICAR_LLM.bat` o comprobar una respuesta web con etiqueta Gemini. |
| Cámara del PC | Pendiente | Se necesita una prueba con el dispositivo real del usuario. |
| GitHub público | Pendiente | No se encontró un repositorio accesible y no hay un enlace público verificado. |
| Video del estudiante | Pendiente | Se entrega guion y guía; falta grabar. |

El alojamiento del sitio se confirma con el resultado de publicación y el enlace proporcionado en la respuesta de entrega. El acceso inicial es privado y debe permitir la evaluación del docente antes de presentar el enlace.

Las pruebas de contratos no miden exactitud de respuestas reales del modelo. La recuperación léxica puede fallar ante paráfrasis complejas. La validación de identificadores evita algunas citas inexistentes, pero no verifica automáticamente que cada afirmación tenga respaldo textual. No se atribuyen porcentajes de precisión ni tiempos de respuesta que no se hayan medido.
