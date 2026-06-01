@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title Aletheia Launcher v1.3

:menu
color 0A
cls
echo ALETHEIA LAUNCHER v1.3 - Cognitive Execution Layer
echo.
echo  [1] DEMO Mode  (DEV  - Mock LLM, rapido)
echo  [2] REAL Mode  (PROD - Ollama llama3.2:3b)
echo  [3] Tests      (CEL + System Tests)
echo  [4] CEL Quick Test
echo  [5] Kill Servers
echo  [0] Exit
echo.
set /p choice="Elije opcion (1-5, 0=salir): "

if "%choice%"=="1" set "MODE=DEV"  & goto prep
if "%choice%"=="2" set "MODE=PROD" & goto prep
if "%choice%"=="3" goto run_tests
if "%choice%"=="4" goto cel_test
if "%choice%"=="5" goto kill_servers
if "%choice%"=="0" exit /b 0
goto menu

:kill_servers
echo Deteniendo servidores...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000 "') do taskkill /f /pid %%a 2>nul
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":3000 "') do taskkill /f /pid %%a 2>nul
taskkill /f /im node.exe 2>nul
echo Servidores detenidos.
pause
goto menu

:prep
set PYTHONIOENCODING=utf-8
echo.

echo [1/3] Instalando dependencias Python...
if exist requirements.txt if not exist .pip-installed (
    pip install -r requirements.txt --quiet
    if %errorlevel% neq 0 (
        echo ERROR: pip install fallo.
        pause
        goto menu
    )
    echo. > .pip-installed
)
echo OK - deps listas.

echo [2/3] Iniciando base de datos...
python cli.py reset
echo OK - DB lista.

echo [3/3] Verificando LLM (Ollama)...
python -c "from ai.ollama_client import healthcheck; h=healthcheck(); print('LLM:', h.get('status'), h.get('models',[])); exit(0 if h.get('status')=='healthy' else 1)"
if %errorlevel% neq 0 (
    echo AVISO: Ollama no responde. Continuando en modo mock...
)

if /i "%MODE%"=="PROD" (
    set "OLLAMA_MODEL=llama3.2:3b"
    echo Modo: PROD - LLM llama3.2:3b
) else (
    set "OLLAMA_MODEL=phi3:mini"
    echo Modo: DEV  - Mock LLM
)

echo.
echo Como quieres interactuar?
echo.
echo   [1] Web   (API + UI en navegador)
echo   [2] Voz   (sesion de voz offline, push-to-talk)
echo.
set /p iface="Elige interfaz (1 o 2): "

if "%iface%"=="1" goto start_web
if "%iface%"=="2" goto start_voice
goto start_web

:start_web
echo.
echo Buscando puertos disponibles...

set "API_PORT="
set "UI_PORT="
for /f %%p in ('python "%~dp0tools\find_port.py" 8000') do set "API_PORT=%%p"
for /f %%p in ('python "%~dp0tools\find_port.py" 3000') do set "UI_PORT=%%p"

if not defined API_PORT (
    echo ERROR: No hay puertos libres cerca del 8000.
    pause & goto menu
)
if not defined UI_PORT (
    echo ERROR: No hay puertos libres cerca del 3000.
    pause & goto menu
)

echo Puerto API: %API_PORT%
echo Puerto UI:  %UI_PORT%
echo.

start "Aletheia API" cmd /k "chcp 65001 >nul & cd /d %~dp0 & set PYTHONIOENCODING=utf-8 & set OLLAMA_MODEL=%OLLAMA_MODEL% & python -m uvicorn core.bootstrap.runtime:app --host 127.0.0.1 --port %API_PORT%"

start "Aletheia UI" cmd /k "chcp 65001 >nul & cd /d %~dp0aletheia-ui & set PORT=%UI_PORT% & npm start"

echo.
echo Esperando que los servidores arranquen (max 90s)...
set "WAIT_ATTEMPTS=0"

:wait_servers
python -c "import socket,sys; s=socket.socket(); s.settimeout(1); r=s.connect_ex(('127.0.0.1',%API_PORT%)); s.close(); sys.exit(0 if r==0 else 1)" >nul 2>&1
if errorlevel 1 goto still_waiting
python -c "import socket,sys; s=socket.socket(); s.settimeout(1); r=s.connect_ex(('127.0.0.1',%UI_PORT%)); s.close(); sys.exit(0 if r==0 else 1)" >nul 2>&1
if not errorlevel 1 goto open_browser

:still_waiting
set /a WAIT_ATTEMPTS+=1
if %WAIT_ATTEMPTS% geq 45 goto open_anyway
timeout /t 2 >nul
goto wait_servers

:open_anyway
echo AVISO: Los servidores tardan mas de lo esperado, abriendo de todas formas...

:open_browser
echo Abriendo navegador...
start http://localhost:%UI_PORT%

echo.
echo Aletheia lanzado!
echo   UI:  http://localhost:%UI_PORT%
echo   API: http://127.0.0.1:%API_PORT%/docs
echo.
pause
goto menu

:start_voice
echo.
echo Arrancando sesion de voz...
echo Tip: abre otra terminal y ejecuta "ollama serve" para respuestas reales.
echo.
set PYTHONIOENCODING=utf-8
set OLLAMA_MODEL=%OLLAMA_MODEL%
python cli.py voice
echo.
echo Sesion de voz finalizada.
pause
goto menu

:run_tests
set PYTHONIOENCODING=utf-8
echo Tests del sistema (puede tardar unos minutos):
python cli.py reset
python cli.py test
pause
goto menu

:cel_test
set PYTHONIOENCODING=utf-8
echo CEL Quick Test:
python -c "from core.orchestrator import process_request; import json; r=process_request('tecnologia','Que es IA?'); print(json.dumps(r, indent=2))"
pause
goto menu
