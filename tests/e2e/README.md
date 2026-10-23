# Pruebas de navegador (Supabase simulado)

Ejecutan la app en Chromium contra un **Supabase simulado** (`mock_supabase.py`) que reproduce Auth,
`app_records` con aislamiento por usuario y la RPC `activate_device_license` de `schema.sql`.
Sirven para probar el código del navegador; **no** prueban las políticas reales de la base.
Para eso use `tests/integracion-supabase.html` con cuentas de prueba.

## Ejecutar

```bash
# desde la raíz del repositorio
python3 -m http.server 8787 --bind 127.0.0.1 &
cd tests/e2e
pip install playwright pillow && python3 -m playwright install chromium
npm install @supabase/supabase-js@2.118.0     # copia local de la librería (la CDN se intercepta)
python3 run_tests.py "commit-o-etiqueta"
```

Necesita también `pdfinfo`, `pdftotext` y `pdfimages` (poppler-utils) para revisar los PDF.

Resultado: `resultados.json` y capturas/PDF en `evidencia/`. Cada prueba queda como
Aprobada, Fallida o Bloqueada; nada se marca como aprobado sin ejecutarse.
