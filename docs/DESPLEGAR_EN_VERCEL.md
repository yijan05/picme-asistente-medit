# Publicar el chatbot de PicMe

La aplicación web se publica desde la raíz del repositorio. El registro de estudiantes y el reconocimiento facial continúan en el programa de escritorio.

## 1. Subir la actualización a GitHub

Extrae el paquete automático y ejecuta `ACTUALIZAR_GITHUB.bat`. El actualizador comprueba el repositorio, guarda un respaldo del código que reemplace, copia los archivos en sus rutas correspondientes y ejecuta commit y push. Cuando muestre `SUBIDA COMPLETA`, continúa con el proyecto de Vercel.

## 2. Crear el proyecto

1. Entra a https://vercel.com/new e inicia sesión con GitHub.
2. Importa el repositorio `yijan05/picme-asistente-medit`. Si no aparece, permite a Vercel acceder a ese repositorio desde su integración con GitHub.
3. Puedes usar `picme-medit` como nombre del proyecto, si está disponible.
4. Selecciona **Next.js** como Framework Preset y deja **Root Directory** en `./`.
5. Conserva los comandos definidos en `vercel.json`. No cambies la carpeta raíz a `desktop`.

## 3. Configurar Gemini antes de publicar

En **Environment Variables**, agrega estas dos variables para **Production**:

| Nombre | Valor |
| --- | --- |
| `GEMINI_API_KEY` | Tu clave privada de Gemini |
| `GEMINI_MODEL` | `gemini-3.5-flash-lite` |

Guarda la clave como **Secret**. Escríbela únicamente en el panel del alojamiento. Si una clave se compartió o publicó anteriormente, reemplázala por una nueva. No uses el prefijo `NEXT_PUBLIC_` para la clave ni la agregues al código o al README.

Selecciona **Deploy** y espera a que termine. Si agregas o cambias las variables después del despliegue, ejecuta **Redeploy** para que se apliquen.

## 4. Comprobar el enlace

Abre la dirección que entregue Vercel y pregunta:

- «Explícame el principio 6».
- «¿Cuáles son los cuatro ejes del MEDIT?».
- «como se si soy una persona tras humana».

La etiqueta **Gemini** en una respuesta confirma que la consulta pasó por el proveedor y superó la validación de formato y referencias. El aviso **Gemini configurado** solamente indica que hay una clave guardada. Si la respuesta dice **Consulta local**, revisa el aviso de respaldo y la configuración.

Comprueba también el enlace de producción en una ventana privada del navegador. El docente debe poder abrirlo y usar el chatbot. Si aparece una pantalla de acceso, revisa **Settings → Deployment Protection** antes de entregar el enlace.

Entrega la dirección real del despliegue, el repositorio público y el video en inglés de máximo cinco minutos. En el video puedes mostrar tanto el chat web como la interfaz de PicMe en tu PC.

## Qué se ajustó

- Las rutas del chat y del estado leen las variables del servidor sin depender del módulo de Cloudflare.
- Vercel compila con Next.js; se conserva la configuración existente de Vinext para el otro alojamiento.
- El modelo predeterminado de la web es `gemini-3.5-flash-lite`.
- La portada usa textos más directos y muestra el número real de artículos.
- La ruta del chat conserva la validación de origen, tamaño y formato. Su contador de solicitudes es temporal y pertenece a cada instancia del servidor; no es un límite global del proveedor.

## Verificación de esta actualización

Se completaron la compilación de producción de Next.js, la revisión de TypeScript y las 13 pruebas del chatbot web. Además, se comprobaron las rutas HTTP del servidor de producción con consulta local y con un proveedor simulado, incluida la consulta de reflexión personal y los rechazos por origen, tamaño o formato inválidos.

La prueba simulada no realiza una llamada real a Google. La conexión real de esta nueva publicación debe comprobarse después de guardar la clave en Vercel. La conexión de Gemini en Windows ya había sido comprobada con HTTP 200.

Referencias de configuración:

- https://vercel.com/docs/git
- https://vercel.com/docs/project-configuration/vercel-json
- https://vercel.com/docs/environment-variables
- https://vercel.com/docs/package-managers
