@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title Aletheia Launcher v1.0

:menu
cls
echo 🧠 ALETHEIA KERNEL LAUNCHER v1.0 - Windows Quick Test
echo.
echo  [1] 🚀 DEMO Mode (DEV - Testing/Simulator - Detect Bugs)
echo  [2] 🔥 REAL Mode (PROD - Live LLM)
echo  [3] ✅ Status ^& Tests Only
echo  [0] Exit
echo.
set /p choice="Elije opcion (1-3, 0=salir): "

if "%choice%"=="1" set "MODE=DEV" ^& goto prep
if "%choice%"=="2" set "MODE=PROD" ^& goto prep
if "%choice%"=="3" goto status
if "%choice%"=="0" exit /b 0
goto menu

:prep
echo.
echo 📦 [1/6] Installing Python dependencies...
pip install -r requirements.txt --quiet --upgrade
if %errorlevel% neq 0 (
    echo ❌ Pip install failed!
    pause
    goto menu
)

echo 🧹 [2/6] Resetting Memory DB...
python cli.py reset
if %errorlevel% neq 0 (
    echo ⚠️ Reset warning, continuing...
)

echo 🧪 [3/6] Running System Tests...
python cli.py test
if %errorlevel% neq 0 (
    echo ❌ Tests FAILED! Fix before launch.
    pause
    goto menu
)
echo ✅ Tests PASSED!

echo 📊 [4/6] Health Status...
python cli.py status

echo.
echo [5/6] Starting Backend API (%MODE% mode) - http://127.0.0.1:8000
start "Aletheia API" cmd /k "cd /d %~dp0 ^& python cli.py start --mode %MODE% --host 127.0.0.1 --port 8000"

echo.
echo [6/6] Starting Frontend UI...
cd aletheia-ui
if not exist "node_modules" (
    echo 📦 Installing NPM deps...
    call npm install
)
start "Aletheia UI" cmd /k "npm start"
cd ..

timeout /t 3 >nul

echo 🌐 Opening Browsers...
start http://127.0.0.1:8000/docs
start http://127.0.0.1:8000/health
start http://localhost:3000

echo ✅ Aletheia launched! Check terminals.
echo 🔄 Re-run launcher.bat anytime.
pause
goto menu

:status
echo 📊 System Status ^& Tests:
python cli.py reset
python cli.py status
python cli.py test
pause
goto menu

