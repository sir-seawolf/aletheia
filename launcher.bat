@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title Aletheia Launcher v1.2

:menu
color 0A
cls
echo ALETHEIA LAUNCHER v1.2 - Cognitive Execution Layer
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

echo [1/4] Instalando dependencias Python...
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

echo [2/4] Iniciando base de datos...
python cli.py reset
echo OK - DB lista.

echo [3/4] Verificando LLM (Ollama)...
python -c "from ai.ollama_client import healthcheck; h=healthcheck(); print('LLM:', h.get('status'), h.get('models',[])); exit(0 if h.get('status')=='healthy' else 1)"
if %errorlevel% neq 0 (
    echo AVISO: Ollama no responde. Continuando en modo mock...
)

echo [4/4] Liberando puertos y arrancando servidores...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000 "') do taskkill /f /pid %%a 2>nul
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":3000 "') do taskkill /f /pid %%a 2>nul
timeout /t 1 >nul

if /i "%MODE%"=="PROD" (
    set "OLLAMA_MODEL=llama3.2:3b"
    echo Modo: PROD - LLM llama3.2:3b
) else (
    set "OLLAMA_MODEL=phi3:mini"
    echo Modo: DEV  - Mock LLM
)

start "Aletheia API" cmd /k "chcp 65001 >nul & cd /d %~dp0 & set PYTHONIOENCODING=utf-8 & set OLLAMA_MODEL=%OLLAMA_MODEL% & python -m uvicorn core.bootstrap.runtime:app --host 127.0.0.1 --port 8000"

pushd aletheia-ui
start "Aletheia UI" cmd /k "npm start"
popd

echo.
echo Esperando que los servidores arranquen...
timeout /t 5 >nul

echo Abriendo navegadores...
start http://localhost:3000
start http://127.0.0.1:8000/docs

echo.
echo Aletheia lanzado!
echo   UI:  http://localhost:3000
echo   API: http://127.0.0.1:8000/docs
echo.
pause
goto menu

:run_tests
set PYTHONIOENCODING=utf-8
echo Tests del sistema (puede tardar ~4 min):
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
