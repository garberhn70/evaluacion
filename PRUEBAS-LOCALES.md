# Ejecutar la versión de pruebas en Windows

## Descarga

Descarga el ZIP de la rama de pruebas:
https://github.com/garberhn70/evaluacion/archive/refs/heads/supabase-integration-prep.zip

Extrae el archivo ZIP en una carpeta local. Entra en la carpeta extraída donde se encuentran `index.html`, `manifest.webmanifest` y `sw.js`.

## Iniciar

1. Haz doble clic en `iniciar-pruebas.bat`.
2. Se abrirá el navegador en `http://127.0.0.1:8787`.
3. No cierres la ventana del servidor mientras haces las pruebas.
4. Inicia sesión con la cuenta y licencia de prueba. Usa solo atletas y resultados ficticios.
5. Para detenerlo, cierra la ventana del servidor o presiona Ctrl+C en ella.

El archivo BAT requiere Python instalado y disponible como `py` o `python`. Si no está instalado, descarga Python desde https://www.python.org/downloads/windows/.

## Qué puedes comprobar localmente

- Acceso y validación de licencia.
- Registro, edición y recuperación de atletas.
- Captura/subida de fotografías (en localhost el navegador considera el contexto local apto para permisos de cámara, sujeto a permisos del equipo).
- Registro de resultados y cálculos.
- Generación de PDF.
- Persistencia en Supabase si hay conexión y la cuenta/licencia autorizan el acceso.
- Pruebas del botón de restablecimiento usando exclusivamente registros ficticios.

## Importante

- Esta carpeta ejecuta la versión de la rama de pruebas; no modifica la página pública de producción.
- Las operaciones autorizadas pueden modificar los datos de la cuenta de pruebas en Supabase. Confirma que estás usando la cuenta y licencia de prueba correctas.
- No introduzcas claves `service_role`; solo se debe usar una clave pública/publishable de Supabase.
- La recuperación de contraseña y la confirmación de alta pueden redirigir al origen local. Si esa función falla por la URL permitida en Supabase Auth, añade `http://127.0.0.1:8787` a Redirect URLs del entorno de prueba.
- Esta ejecución local no equivale a una prueba automatizada de extremo a extremo. Registra los resultados en `panel_visual_pruebas_voleibol.html` o en el panel visual que ya tienes.

## Resultados automáticos

La rama también contiene pruebas estáticas en `tests/smoke-test.mjs`, ejecutadas por GitHub Actions. Pasarlas valida sintaxis y presencia de flujos críticos; no confirma todos los comportamientos del navegador.
