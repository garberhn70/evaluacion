@echo off
setlocal
title Evaluacion Fisica de Voleibol - pruebas locales
cd /d "%~dp0"

where py >nul 2>&1
if %errorlevel%==0 (
  set "PYTHON_CMD=py"
) else (
  where python >nul 2>&1
  if not %errorlevel%==0 (
    echo.
    echo ERROR: Python no esta instalado o no esta disponible en PATH.
    echo Instale Python desde https://www.python.org/downloads/windows/
    echo y vuelva a ejecutar este archivo.
    echo.
    pause
    exit /b 1
  )
  set "PYTHON_CMD=python"
)

echo Iniciando servidor local de prueba en http://127.0.0.1:8787
echo Mantenga esta ventana abierta mientras utiliza la aplicacion.
echo Para detener el servidor, presione Ctrl+C.
start "Servidor local voleibol" cmd /k "cd /d ""%~dp0"" && %PYTHON_CMD% -m http.server 8787 --bind 127.0.0.1"
timeout /t 2 /nobreak >nul
start "" http://127.0.0.1:8787
endlocal
