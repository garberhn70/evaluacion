# Pruebas de Evaluación Física de Voleibol

## Validación automática

En cada push a `supabase-integration-prep` y en los pull requests hacia `main`, GitHub Actions ejecuta:

```bash
node tests/smoke-test.mjs
```

El script verifica la sintaxis de los bloques JavaScript embebidos, presencia de controles críticos, rutas de autenticación/licencia, límites de usuario en las consultas de registros, el doble paso de confirmación del restablecimiento, fotografía, PDF, manifiesto y recursos locales.

**Importante:** estas son comprobaciones estáticas. No sustituyen las pruebas en navegador ni las pruebas de integración reales contra Supabase. Una validación automática aprobada no confirma inicio de sesión, licencia, sincronización, permisos efectivos o borrado real.

La aplicación también utiliza Supabase Realtime para recibir cambios de `app_records` entre sesiones. La publicación `supabase_realtime` ya fue comprobada y la tabla está habilitada en el proyecto de pruebas. La configuración queda documentada en `supabase/migrations/20261023070000_add_app_records_to_supabase_realtime.sql`; al verificar otro proyecto Supabase, confirma que esta migración se haya ejecutado.

## Pruebas manuales antes de publicar

1. Ejecutar login válido e inválido y cierre de sesión.
2. Probar activación de licencia válida/incorrecta y límites de dispositivos.
3. Crear, editar, guardar, recuperar y borrar atletas de prueba.
4. Guardar y volver a cargar fotografías.
5. Comprobar resultados, cálculos y evaluaciones de las pruebas físicas.
6. Generar PDF individual y de equipo; comparar sus datos contra el registro.
7. Probar persistencia después de recargar y en una segunda sesión autorizada; confirmar que una modificación de una sesión aparece en la otra mediante Realtime.
8. Verificar aislamiento entre cuentas.
9. Probar ambas cancelaciones del restablecimiento.
10. Ejecutar el restablecimiento solo con datos ficticios y confirmar el estado en Supabase después de recargar.

## Registro de incidencias

Por cada prueba manual, anotar fecha, versión/commit, pasos, resultado esperado, resultado real, estado (Pendiente, En proceso, Aprobada, Fallida o Bloqueada) y evidencia. No marcar como aprobada una prueba que no se haya ejecutado.

## Seguridad

- No introducir claves `service_role` en HTML/JavaScript del navegador.
- No hacer pruebas destructivas con datos reales.
- No fusionar ni publicar hasta revisar todos los fallos críticos.


## Ejecutar una versión local de pruebas

Consulta `PRUEBAS-LOCALES.md`. En Windows, descarga el ZIP de la rama de pruebas, extrae los archivos y ejecuta `iniciar-pruebas.bat`. Esto inicia un servidor local sin modificar la publicación de producción. Usa exclusivamente una cuenta/licencia de prueba y datos ficticios.
