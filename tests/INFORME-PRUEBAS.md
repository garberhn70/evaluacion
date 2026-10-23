# Informe de pruebas — rama `supabase-integration-prep`

Fecha: 23/10/2026 · Navegador: Chromium (Playwright) · Supabase **simulado** (`tests/e2e/mock_supabase.py`)

**Resumen:** pruebas de navegador: 46 aprobadas, 0 fallidas (2 se cubren con el Supabase real) · pruebas contra el Supabase real (23/10/2026): 21 aprobadas, 0 fallidas. Sin pruebas bloqueadas.

> Las pruebas automáticas prueban el código del navegador (sesión, licencia, guardado, trabajo sin conexión, fotos, PDF,
> restablecimiento y fallos de red). **No** prueban las políticas reales de la base: para eso está
> `tests/integracion-supabase.html`, ejecutado el 23/10/2026 con dos cuentas y una licencia de prueba (ver abajo).

## Errores encontrados y corregidos

| # | Problema | Causa | Corrección | Prueba |
|---|---|---|---|---|
| 1 | Después de iniciar sesión la app **siempre volvía a pedir la licencia** | El código se guardaba como texto y se leía como JSON | Lectura con `localStorage.getItem` | A1, A2 |
| 2 | iPad/celular quedaba registrado como **computadora** | El tipo de dispositivo no se guardaba | Se guarda `vb-device-type` y se detecta solo | A7 |
| 3 | «Elegir fotografía» en iPad/celular **abría solo la cámara** | `capture="user"` | Se quitó `capture` | D4 |
| 4 | Se perdía la foto de un atleta nuevo al cambiar momento/temporada | La foto se reiniciaba en cada cambio | Solo se reinicia al cambiar de atleta | D5 |
| 5 | Promedio del comparativo redondeado (45 → 49) con % sin redondear | 0 decimales en promedios | Un decimal más | F2 |
| 6 | Mensajes en inglés (cámara, inicio de sesión) | Se mostraba el error técnico | Mensajes en español | A4, A10, D7 |
| 7 | **Sin internet la app no se podía usar** y mostraba datos viejos | La pantalla de acceso bloqueaba todo y no había copia de la nube en el equipo | **Modo sin conexión** (abajo) | O1–O7, E2, E3 |
| 8 | `supabase-js` se cargaba de la CDN sin versión fija y no funcionaba sin internet | `@supabase/supabase-js@2` externo | Versión fija `2.118.0` con huella SRI; el service worker la guarda para usarla sin conexión | O8 y estática |

## Modo sin conexión (nuevo)

- Al trabajar conectado, el equipo guarda una copia de los datos de la cuenta.
- Si al abrir no hay internet, la app entra con esa copia (si la licencia se validó en ese equipo en los últimos **30 días**).
- Lo que se registra o borra sin internet queda en una **cola** y se sube solo al volver la conexión (gana el último cambio de cada registro).
- El estado muestra «Sin conexión · N cambios por subir».
- Sin conexión no se permite «Restablecer toda la información».
- «Cerrar sesión» avisa si hay cambios sin subir.
- La primera vez en un equipo sí se necesita internet.

## Normas por edad y sexo (nuevo, aprobado por la entrenadora el 23/10/2026)

- La app elige la norma según la **edad del atleta el día de la evaluación** y su rama. Cada nivel muestra su fuente.
- **Salto horizontal:** FitBack 2023 (Tomkinson et al., BJSM), 12 a 18 años; 18 en adelante usa la fila de 18 (estimado).
- **Salto vertical CMJ con manos en la cintura (prueba nueva, 3 intentos):** Polakovičová et al. 2018, voleibol juvenil de élite, 13 a 19 años.
- **Sprint de 10 m, rama femenina:** Oliveira et al. 2025, clubes de Portugal (11–15 años y 16 en adelante). Rama masculina: referencia interna.
- **T-test, 16 años en adelante:** tabla para deportistas adultos de equipo; el corte de Bajo es estimado (+1 s). Menores de 16: referencia interna.
- **IMC de 5 a 18 años:** puntaje z de la OMS 2007 (coeficientes LMS oficiales). Verificado aparte: 14 años 6 meses, IMC 20,76 → z +0,28.
- Cortes: Bajo = P25, Medio = P50, Bueno = P75, Excelente = P95.
- **Referencia interna** (sin norma internacional): bloqueo, ataque, 5 m, sentadilla, balón medicinal, plancha, Yo-Yo y burpees. Plancha y burpees se conservan.
- Cada norma se puede desactivar en «Referencias de nivel físico»; entonces se usa la referencia interna editable. La elección se guarda en la cuenta.
- Las evaluaciones guardadas no cambian; solo se recalcula el nivel mostrado.

## Decisiones tomadas (se pueden cambiar)

- Sin conexión se puede **ver y registrar**; límite de 30 días sin validar licencia.
- El restablecimiento **no** borra la copia de Google Drive; el aviso de confirmación lo dice.

## Pendiente (requiere acción del administrador)

1. Revisar y aplicar `supabase/propuestas/PROPUESTA_licencia_en_rls.sql`: hoy la base no exige licencia (solo la pantalla) y un
   dispositivo revocado se reactiva solo. **No aplicada.**
2. Realtime en vivo no se pudo simular (E4 se comprobó con recarga).

## Resultados

| ID | Prueba | Esperado | Obtenido | Estado |
|---|---|---|---|---|
| A1 | Inicio de sesión válido con licencia válida | Entra a la app, estado «Conectado a la base de datos centralizada» | Puerta visible al abrir: True. Tras iniciar: puerta visible=False, estado='Conectado a la base de datos centralizada'. Corrección aplicada antes: lectura del código de licencia. | **Aprobada** |
| A2 | Persistencia de sesión al recargar | Sigue conectado | Tras recargar sigue conectado sin volver a pedir datos | **Aprobada** |
| A3 | Cierre de sesión | Vuelve a la pantalla de acceso | Vuelve la pantalla de acceso; el código de licencia guardado se borra | **Aprobada** |
| A4 | Rechazo de credenciales incorrectas | Mensaje de error, no entra | Rechazada con mensaje: «Correo o contraseña incorrectos.» | **Aprobada** |
| A5 | Rechazo de licencia inválida | No entra; «Código de licencia no válido.» | Rechazada: «Código de licencia no válido.» | **Aprobada** |
| A6 | Licencia vencida | No entra; mensaje de vigencia | Rechazada: «Licencia vencida o fuera de vigencia.» | **Aprobada** |
| A7 | Límite de dispositivos | 2.ª computadora rechazada; celular aceptado | Segunda computadora: «Ya se alcanzó el límite de dispositivos de este tipo. Libera uno o contacta al administrador.». Un celular con la misma licencia: entra (cupo 1 computadora + 1 celular). | **Aprobada** |
| A8 | Licencia de otra cuenta | Rechazo «pertenece a otra cuenta» | Rechazada: «La licencia pertenece a otra cuenta.» | **Aprobada** |
| A9 | Error del servidor al validar licencia | No entra y muestra el error | Error 500 del servidor: queda en la pantalla de acceso con «Error interno simulado» y estado «Licencia no validada»; no se muestra como éxito. | **Aprobada** |
| A10 | Primer uso sin internet | No entra y explica el motivo | Primer uso sin internet (sin copia previa): sigue la pantalla de acceso con el mensaje «No hay conexión a internet. La primera vez en este equipo se necesita internet para validar la cuenta y la licencia.». Es lo esperado: la primera vez hay que validar la cuenta y la licencia con conexión. | **Aprobada** |
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
| E2 | Corte de conexión al guardar | Se guarda en este equipo, queda en cola y se avisa | Con la conexión cortada al guardar: «Guardado: Atleta Sin Red, pretemporada (línea base) 2026. Quedó en este equipo y se subirá a la nube al volver internet.». Pendientes en la cola: 2. Estado: «Sin conexión: trabajando con la copia de este equipo · 2 cambios por subir. Se sincroniza al volver internet.». Nada llegó a la nube todavía (0). | **Aprobada** |
| E3 | Sincronización al volver la conexión | La cola se sube sola | Al volver la conexión se subió solo: en la nube 1, en cola 0, estado «Conectado a la base de datos centralizada» | **Aprobada** |
| E4 | Cambios de otra sesión | Aparece | Un cambio hecho en otra sesión aparece al recargar (Realtime en vivo no se puede simular aquí) | **Aprobada** |
| O1 | Abrir la app sin internet tras trabajar en la nube | Abre con la copia de este equipo | Sin internet al abrir: pantalla de acceso visible=False; estado «Sin conexión: trabajando con la copia de este equipo. Se sincroniza al volver internet.»; atletas de la nube disponibles: sí | **Aprobada** |
| O2 | Registrar sin internet | Se guarda en el equipo y queda en cola | Evaluación nueva sin internet: «Guardado: Atleta Offline, pretemporada (línea base) 2026. Quedó en este equipo y se subirá a la nube al volver internet.»; en cola 2 | **Aprobada** |
| O3 | Borrar sin internet | Se borra en el equipo y queda en cola | Borrado sin internet: desaparece en el equipo y queda en cola (la nube aún lo tiene) | **Aprobada** |
| O4 | Restablecer sin internet | No se permite | «Para restablecer se necesita conexión a internet. Conéctese e intente de nuevo.» | **Aprobada** |
| O5 | Cerrar sesión con cambios sin subir | Avisa y no pierde cambios | Con 4 cambios sin subir, «Cerrar sesión» pide confirmación; al cancelar sigue dentro y no se pierde nada | **Aprobada** |
| O6 | Subir lo hecho sin internet | Altas y borrados llegan a la nube | Al volver internet: se subió el atleta nuevo y se aplicó el borrado; cola 0; estado «Conectado a la base de datos centralizada»; tras recargar coincide: True | **Aprobada** |
| O7 | Límite de días sin conexión | Pide conexión | Con la última validación de licencia de hace 31 días, sin internet no deja entrar (límite: 30 días) | **Aprobada** |
| O8 | Sin internet ni librería en caché | Abre con la copia del equipo | Sin internet y sin poder cargar la librería: entra con la copia del equipo («Sin conexión: trabajando con la copia de este equipo. Se sin…») | **Aprobada** |
| E6 | Aislamiento real entre cuentas (RLS) | Sin acceso a datos ajenos | Aprobada en el Supabase real: la cuenta B no ve, no modifica ni borra los registros de A, y no puede usar su licencia (I17–I20). | **Aprobada** |
| E7 | Permisos de licencias y license_devices | Sin acceso a datos ajenos | Aprobada en el Supabase real: sin sesión y con sesión no se pueden leer licenses ni license_devices; la RPC exige sesión; inserciones ajenas y colecciones no permitidas se rechazan (I01–I05, I13–I15). | **Aprobada** |
| F1 | Ficha individual con foto | Nombre, foto, valores y % correctos | Ficha_Ana_Ficticia_2026.pdf: 2 página(s), 1 imagen(es). Bloqueo pre 50 cm, fin 55 cm y cambio +10 % presentes: True | **Aprobada** |
| F2 | Informe del equipo y comparativo por etapas | 1 página resumen + 1 por prueba; promedios y % correctos | 12 páginas (resumen + 11 pruebas), 11 imágenes. Bloqueo: Ana 50→55 (+10 %): True; Bea 40→42 (+5 %): True; promedio 45→48,5 (+7,8 %): True | **Aprobada** |
| F3 | Informe de atleta sin foto | Se genera sin error | Atleta sin foto: el informe se genera y muestra «Sin foto» (4 páginas) | **Aprobada** |
| G1 | Cancelar la primera confirmación | Nada se borra | Cancelado en la 1.ª confirmación: 6 registros intactos | **Aprobada** |
| G2 | Palabra de confirmación incorrecta | Nada se borra | Palabra incorrecta («borrar»): «Operación cancelada. No se borró ningún dato.», 6 registros intactos | **Aprobada** |
| G3 | Fallo de conexión durante el borrado | Error visible, sin borrado parcial ni falso éxito | Con la red cortada: «No se pudo completar el borrado. Revise la conexión y vuelva a intentarlo. Detalle: TypeEr…»; base y pantalla intactas | **Aprobada** |
| G4 | Borrado confirmado con BORRAR | Se borran solo los datos de la cuenta; sesión y licencia siguen | «Información restablecida. El registro está vacío y listo para comenzar las pruebas.». Registros del usuario: 6→0; los de otra cuenta se conservan (1). Tras recargar no reaparecen; sesión y licencia conservadas: True. | **Aprobada** |
| D6 | Capturar con la cámara | Vista previa con la foto | Cámara simulada: video visible True; foto capturada True | **Aprobada** |
| D7 | Permiso de cámara denegado | Mensaje claro | Permiso de cámara negado: «No se encontró una cámara en este equipo. Use «Elegir fotografía».» | **Aprobada** |
| N1 | Prueba nueva: salto vertical CMJ | Aparece el CMJ con 3 intentos | La ficha tiene el Salto vertical CMJ con 3 intentos y sin errores de página | **Aprobada** |
| N2 | Nivel con norma por edad (18 años) | Niveles de la norma de 18 años con la fuente | 18 años, rama femenina: horizontal 190 = Bueno (FitBack), CMJ 33 = Medio, 10 m 1,95 = Medio, T-test 11,0 = Bueno, cada uno con su fuente | **Aprobada** |
| N3 | Norma según la edad (14 años) e IMC OMS | Tabla de 14 años; T-test con referencia interna; z de IMC +0,3 | 14 años: horizontal = Bueno (tabla de 14), 10 m = Bueno (Sub-13 a Sub-16), T-test sin norma usa la referencia interna (Medio); IMC 20,8 → z +0,3 normal (OMS) | **Aprobada** |
| N4 | Desactivar una norma | Vuelve a la referencia interna y se recuerda | Las 4 normas se ven con su fuente; al desmarcar la de salto horizontal se usa la referencia interna (190 = Medio), se guarda en la cuenta y sigue así al recargar | **Aprobada** |
| N5 | IMC de adulto | Categoría de adulto | Adulta de 28 años: IMC con categorías de adulto (Normal), sin puntaje OMS; sin errores de página | **Aprobada** |

## Pruebas contra el Supabase real (23/10/2026)

Ejecutadas por el administrador con `tests/integracion-supabase.html` (cuentas y licencia de prueba). Datos crudos: `tests/resultados-integracion-supabase.json`.

| ID | Prueba | Esperado | Obtenido | Estado |
|---|---|---|---|---|
| I01 | Lectura anónima de app_records | 0 filas o error de permisos | 0 filas | **Aprobada** |
| I02 | Lectura anónima de licenses | 0 filas o error de permisos | Error: permission denied for table licenses | **Aprobada** |
| I03 | Lectura anónima de license_devices | 0 filas o error de permisos | Error: permission denied for table license_devices | **Aprobada** |
| I04 | RPC de licencia sin sesión | Rechazo (sin permiso o «Debes iniciar sesión») | Error: permission denied for function activate_device_license | **Aprobada** |
| I05 | Inserción anónima en app_records | Rechazo por RLS | Rechazada: new row violates row-level security policy for table "app_records" | **Aprobada** |
| I06 | Inicio de sesión cuenta A | Sesión válida | Usuario d001b107-5d50-4e9a-85a9-c3e02e483f16 | **Aprobada** |
| I07 | Contraseña incorrecta | Rechazo | Rechazada: Invalid login credentials | **Aprobada** |
| I08 | Licencia válida en un dispositivo de prueba | ok: true | {"ok":true,"status":"active","expires_at":"2027-01-23T14:19:44.242284+00:00"} | **Aprobada** |
| I09 | Licencia inválida | ok: false | {"ok":false,"message":"Código de licencia no válido."} | **Aprobada** |
| I10 | Guardar registro ficticio | Sin error | Guardado | **Aprobada** |
| I11 | Leer el registro guardado | 1 fila con v=1 | [{"data":{"v":1,"nombre":"Atleta de integración"}}] | **Aprobada** |
| I12 | Actualizar el registro | v=2 al releer | [{"data":{"v":2,"nombre":"Atleta de integración"}}] | **Aprobada** |
| I13 | Insertar con el user_id de otra persona | Rechazo por RLS | Rechazada: new row violates row-level security policy for table "app_records" | **Aprobada** |
| I14 | Leer licenses estando conectada | 0 filas o error (no debe ver códigos) | Error: permission denied for table licenses | **Aprobada** |
| I15 | Colección no permitida | Rechazo por la restricción check | Rechazada: new row for relation "app_records" violates check constraint "app_records_collection_check" | **Aprobada** |
| I16 | Inicio de sesión cuenta B | Sesión válida | Usuario 02e24bd8-e22e-4257-9ca2-306a837bd0ae | **Aprobada** |
| I17 | B intenta leer los registros de A | 0 filas | 0 filas visibles | **Aprobada** |
| I18 | B intenta modificar el registro de A | A conserva v=2 | Valor en A: {"v":2,"nombre":"Atleta de integración"} | **Aprobada** |
| I19 | B intenta borrar el registro de A | El registro de A sigue existiendo | Filas de A: 1 | **Aprobada** |
| I20 | B intenta usar la licencia de A | ok: false («pertenece a otra cuenta») | {"ok":false,"message":"La licencia pertenece a otra cuenta."} | **Aprobada** |
| I21 | Borrar el registro ficticio | 0 filas al releer | Quedan 0 | **Aprobada** |
| NOTA | Dispositivo de prueba registrado | — | La prueba I08 registró el dispositivo «dispositivo-prueba-oepppgxm» en license_devices. Si su licencia de prueba permite solo 1 computadora, revóquelo en Supabase (revoked_at) antes de usar otra. | **Omitida** |

## Cómo repetir

- Pruebas automáticas: `tests/e2e/README.md`.
- Contra Supabase real: `iniciar-pruebas.bat` y abrir `http://127.0.0.1:8787/tests/integracion-supabase.html`.
- Datos crudos: `tests/resultados-automaticos.json`.
