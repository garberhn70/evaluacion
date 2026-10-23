@echo off
setlocal
title Evaluacion Fisica de Voleibol - pruebas locales
cd /d "%~dp0"

rem Se comprueba que Python realmente funcione (el acceso directo de la Tienda de Microsoft no sirve)
set "PYTHON_CMD="
py -3 -V >nul 2>&1 && set "PYTHON_CMD=py -3"
if not defined PYTHON_CMD python -V >nul 2>&1 && set "PYTHON_CMD=python"
if not defined PYTHON_CMD (
  echo.
  echo ERROR: Python no esta instalado en este equipo.
  echo Instale Python desde https://www.python.org/downloads/windows/
  echo y marque la casilla "Add Python to PATH" durante la instalacion.
  echo Luego vuelva a ejecutar este archivo.
  echo.
  pause
  exit /b 1
)

echo Iniciando servidor local de prueba en http://127.0.0.1:8787
echo Mantenga esta ventana abierta mientras utiliza la aplicacion.
echo Para detener el servidor, cierre esta ventana o presione Ctrl+C.
echo.
echo Pruebas contra Supabase: http://127.0.0.1:8787/tests/integracion-supabase.html
echo.
start "" /b cmd /c "timeout /t 2 /nobreak >nul & start http://127.0.0.1:8787"
%PYTHON_CMD% -m http.server 8787 --bind 127.0.0.1
echo.
echo El servidor se detuvo. Si aparece un error arriba, envielo a soporte.
pause
