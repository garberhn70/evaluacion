# Informe de pruebas — rama `supabase-integration-prep`

Fecha: 23/10/2026 · Base probada: commit `ef0ab54` + correcciones de este informe · Navegador: Chromium (Playwright)

**Resumen:** 32 aprobadas · 2 fallidas · 2 bloqueadas · 36 en total.

> Las pruebas automáticas usan un **Supabase simulado** (`tests/e2e/mock_supabase.py`). Prueban el código del navegador
> (sesión, licencia, guardado, fotos, PDF, restablecimiento, fallos de red), **no** las políticas reales de la base.
> Las pruebas contra el proyecto real están en `tests/integracion-supabase.html` y quedan **bloqueadas** hasta que se ejecuten
> con cuentas de prueba.

## Errores encontrados y corregidos

| # | Problema | Causa | Corrección | Prueba que lo confirma |
|---|---|---|---|---|
| 1 | Después de iniciar sesión la app **siempre volvía a pedir la licencia**; nunca se llegaba a la base de datos | El código se guardaba como texto simple y se leía con `local.get`, que espera JSON: la lectura fallaba y devolvía vacío | Leer `vb-license-code` con `localStorage.getItem` | A1, A2 (antes fallaban) |
| 2 | En iPad/celular el dispositivo se registraba como **computadora** y ocupaba ese cupo | El tipo elegido no se guardaba; al recargar volvía a «Computadora» | Se guarda `vb-device-type` al iniciar sesión y se detecta automáticamente en celulares/iPad | A7 |
| 3 | «Elegir fotografía» en iPad/celular **abría solo la cámara**, sin galería | `capture="user"` en el selector de archivo | Se quitó `capture` (la cámara sigue en «Tomar fotografía») | D4 |
| 4 | La foto de un atleta nuevo **se perdía** al cambiar momento o temporada antes de guardar | `loadEvalForm` reiniciaba la foto en cada cambio | Solo se reinicia al cambiar de atleta | D5 |
| 5 | En el comparativo del equipo el promedio aparecía redondeado (45 → 49) con un % calculado sin redondear (+7,8 %) | Promedios con 0 decimales | Promedios con un decimal más (45,0 → 48,5) | F2 |
| 6 | Mensajes de cámara en inglés («Requested device not found») | Se mostraba el error del navegador | Mensajes en español para permiso negado, sin cámara y cámara ocupada | D7 |

Se agregaron 3 comprobaciones a `tests/smoke-test.mjs` para que estos errores no vuelvan (15/15 aprobadas).

## Pendiente de decisión (no corregido)

1. **Sin internet la app queda inutilizable (A10, E5).** La pantalla de acceso tapa toda la aplicación y no tiene opción de
   continuar. Además, en modo nube no se guarda copia local: sin conexión, detrás aparecen datos antiguos del equipo, no lo
   trabajado en la nube. Para canchas sin internet esto es crítico. Propuesta: guardar una copia local de lo descargado de la
   nube y agregar «Trabajar sin conexión (solo lectura)» o con cola de cambios. Afecta la regla de licencias, por eso necesita
   su aprobación.
2. **La licencia no se exige en la base de datos.** Las políticas RLS de `app_records` solo comparan `auth.uid() = user_id`.
   Cualquier cuenta nueva (el alta está abierta) puede leer y escribir sus propios registros por la API sin licencia.
   Propuesta en `supabase/propuestas/PROPUESTA_licencia_en_rls.sql` (**no aplicada**).
3. **Un dispositivo revocado se reactiva solo** al volver a abrir la app (`on conflict … revoked_at = null`). Incluido en la misma propuesta.
4. **`supabase-js` se carga desde la CDN sin versión fija** (`@supabase/supabase-js@2`) y el service worker no lo guarda.
   Recomendado fijar la versión (por ejemplo `@2.118.0`) y decidir si se guarda para uso sin conexión.
5. **El restablecimiento no borra la copia en Google Drive** (respaldo automático de la versión publicada). Es razonable como
   respaldo, pero «Traer último respaldo de la nube» podría devolver los datos borrados. Confirmar si es lo deseado.
6. **Realtime** no se pudo probar en vivo (simulado solo con recarga, E4).

## Resultados

| ID | Prueba | Esperado | Obtenido | Estado |
|---|---|---|---|---|
| A1 | Inicio de sesión válido con licencia válida | Entra a la app, estado «Conectado a la base de datos centralizada» | Puerta visible al abrir: True. Tras iniciar: puerta visible=False, estado='Conectado a la base de datos centralizada'. Corrección aplicada antes: lectura del código de licencia. | **Aprobada** |
| A2 | Persistencia de sesión al recargar | Sigue conectado | Tras recargar sigue conectado sin volver a pedir datos | **Aprobada** |
| A3 | Cierre de sesión | Vuelve a la pantalla de acceso | Vuelve la pantalla de acceso; el código de licencia guardado se borra | **Aprobada** |
| A4 | Rechazo de credenciales incorrectas | Mensaje de error, no entra | Rechazada con mensaje: «Invalid login credentials» | **Aprobada** |
| A5 | Rechazo de licencia inválida | No entra; «Código de licencia no válido.» | Rechazada: «Código de licencia no válido.» | **Aprobada** |
| A6 | Licencia vencida | No entra; mensaje de vigencia | Rechazada: «Licencia vencida o fuera de vigencia.» | **Aprobada** |
| A7 | Límite de dispositivos | 2.ª computadora rechazada; celular aceptado | Segunda computadora: «Ya se alcanzó el límite de dispositivos de este tipo. Libera uno o contacta al administrador.». Un celular con la misma licencia: entra (cupo 1 computadora + 1 celular). | **Aprobada** |
| A8 | Licencia de otra cuenta | Rechazo «pertenece a otra cuenta» | Rechazada: «La licencia pertenece a otra cuenta.» | **Aprobada** |
| A9 | Error del servidor al validar licencia | No entra y muestra el error | Error 500 del servidor: queda en la pantalla de acceso con «Error interno simulado» y estado «Licencia no validada»; no se muestra como éxito. | **Aprobada** |
| A10 | Uso sin internet (sin acceso a Supabase) | Poder seguir trabajando o al menos ver los datos guardados | Sin conexión a la CDN de Supabase: estado «Modo local: configure la conexión para sincronizar», mensaje al iniciar «No se pudo cargar Supabase JS. Compruebe Internet.». La pantalla de acceso tapa toda la app y no hay opción para trabajar sin conexión, aunque los datos locales están cargados detrás. | **Fallida** |
| B1 | Campo obligatorio: nombre | Mensaje y nada guardado | Sin nombre: «Escriba el nombre del atleta.»; no se creó ningún registro | **Aprobada** |
| B2 | Crear atleta y guardar sin duplicados | Un solo atleta y una sola evaluación | 1 atleta y 1 evaluación en la base simulada tras doble toque en Guardar; mensaje «Guardado: Atleta Ficticia Uno, pretemporada (línea base) 2026.» | **Aprobada** |
| C1 | Fórmulas con valores conocidos | Coinciden con el cálculo manual | Todos los resultados coinciden con el cálculo manual: bloqueo 265−215=50 cm (potencia 60,7·50+45,3·60−2055=3.698 W), ataque 285−220=65 cm, sentadilla Brzycki 60·36/(37−5)=67,5→68 kg, IMC 60/1,7²=20,8. | **Aprobada** |
| C2 | Valores incorrectos e incompletos | Mensajes de error, sin resultados falsos | Valores incorrectos se marcan: salto menor que el alcance, más de 10 repeticiones y peso no numérico (IMC no se calcula) | **Aprobada** |
| B3 | Editar y recuperar tras recargar | Se ven los datos nuevos | Edición guardada en la base y recuperada tras recargar (posición Central, peso 61) | **Aprobada** |
| D1 | Elegir imagen, vista previa y quitar | Vista previa y retiro correcto | Vista previa en JPEG comprimido; «Quitar fotografía» la retira antes de guardar | **Aprobada** |
| D2 | Imagen grande: compresión, guardado y recuperación | Se reduce (≤480 px) y reaparece | Foto de 4000×3000 guardada como 480×360 (2 KB) y recuperada tras recargar: True | **Aprobada** |
| D3 | Formatos no válidos | Mensajes claros, sin romper la ficha | Texto: «Seleccione un archivo de imagen.». PNG dañado: «No se pudo leer la imagen.» | **Aprobada** |
| D4 | «Elegir fotografía» en celular/iPad | Permite elegir de la galería | Sin atributo capture | **Aprobada** |
| D5 | Foto de atleta nuevo al cambiar momento | La foto se mantiene | La foto se conserva al cambiar el momento | **Aprobada** |
| B4 | Eliminar atleta de prueba | Desaparece de la base y de la pantalla | Atleta y sus evaluaciones borrados de la base; no reaparecen al recargar | **Aprobada** |
| E2 | Corte de conexión al guardar | Mensaje de error, sin falso éxito | Con la conexión cortada al guardar: «No se pudo guardar. Revise la conexión e intente de nuevo.». No se muestra como guardado. | **Aprobada** |
| E3 | Recuperación al volver la conexión | Se guarda | Al volver la conexión y guardar de nuevo: «Guardado: Atleta Sin Red, pretemporada (línea base) 2026.» | **Aprobada** |
| E4 | Cambios de otra sesión | Aparece | Un cambio hecho en otra sesión aparece al recargar (Realtime en vivo no se puede simular aquí) | **Aprobada** |
| E5 | Abrir la app sin conexión tras trabajar en la nube | Ver los datos más recientes o un aviso claro | Sin conexión al abrir: estado «Licencia no validada», pantalla de acceso tapando la app: True. Atletas cargados detrás: los antiguos/locales, NO los de la nube. En modo nube no se guarda copia local, así que sin internet no se puede ver lo trabajado. | **Fallida** |
| E6 | Aislamiento real entre cuentas (RLS) | — | Necesita dos cuentas de prueba en el Supabase real. Desde aquí no tengo permiso para conectarme a su proyecto. | **Bloqueada** |
| E7 | Permisos de licencias y license_devices | — | Necesita el Supabase real (políticas y función activate_device_license). | **Bloqueada** |
| F1 | Ficha individual con foto | Nombre, foto, valores y % correctos | Ficha_Ana_Ficticia_2026.pdf: 2 página(s), 1 imagen(es). Bloqueo pre 50 cm, fin 55 cm y cambio +10 % presentes: True | **Aprobada** |
| F2 | Informe del equipo y comparativo por etapas | 1 página resumen + 1 por prueba; promedios y % correctos | 12 páginas (resumen + 11 pruebas), 11 imágenes. Bloqueo: Ana 50→55 (+10 %): True; Bea 40→42 (+5 %): True; promedio 45→48,5 (+7,8 %): True | **Aprobada** |
| F3 | Informe de atleta sin foto | Se genera sin error | Atleta sin foto: el informe se genera y muestra «Sin foto» (4 páginas) | **Aprobada** |
| G1 | Cancelar la primera confirmación | Nada se borra | Cancelado en la 1.ª confirmación: 6 registros intactos | **Aprobada** |
| G2 | Palabra de confirmación incorrecta | Nada se borra | Palabra incorrecta («borrar»): «Operación cancelada. No se borró ningún dato.», 6 registros intactos | **Aprobada** |
| G3 | Fallo de conexión durante el borrado | Error visible, sin borrado parcial ni falso éxito | Con la red cortada: «No se pudo completar el borrado. Revise la conexión y vuelva a intentarlo. Detalle: TypeEr…»; base y pantalla intactas | **Aprobada** |
| G4 | Borrado confirmado con BORRAR | Se borran solo los datos de la cuenta; sesión y licencia siguen | «Información restablecida. El registro está vacío y listo para comenzar las pruebas.». Registros del usuario: 6→0; los de otra cuenta se conservan (1). Tras recargar no reaparecen; sesión y licencia conservadas: True. | **Aprobada** |
| D6 | Capturar con la cámara | Vista previa con la foto | Cámara simulada: video visible True; foto capturada True | **Aprobada** |
| D7 | Permiso de cámara denegado | Mensaje claro | Permiso de cámara negado: «No se encontró una cámara en este equipo. Use «Elegir fotografía».» | **Aprobada** |

## Cómo repetir

- Pruebas automáticas: `tests/e2e/README.md`.
- Pruebas contra Supabase real: abrir `tests/integracion-supabase.html` con `iniciar-pruebas.bat`
  (`http://127.0.0.1:8787/tests/integracion-supabase.html`), escribir dos cuentas de prueba y una licencia de prueba.
- Datos crudos: `tests/resultados-automaticos.json`.
