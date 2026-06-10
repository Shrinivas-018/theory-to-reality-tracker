@echo off
title Idea Evolution Tracker Launcher
setlocal enabledelayedexpansion

echo =========================================================
echo    THEORY-TO-REALITY EVOLUTION TRACKER LAUNCHER
echo =========================================================
echo.

:: Detect Python Virtual Environment
set VENV_PATH=
if exist "%~dp0..\..\..\.venv\Scripts\python.exe" (
    set "VENV_PATH=%~dp0..\..\..\.venv"
) else if exist "%~dp0.venv\Scripts\python.exe" (
    set "VENV_PATH=%~dp0.venv"
) else if exist "%~dp0..\.venv\Scripts\python.exe" (
    set "VENV_PATH=%~dp0..\.venv"
)

if not "!VENV_PATH!"=="" (
    set "PYTHON_EXE=!VENV_PATH!\Scripts\python.exe"
    echo [OK] Found Python Virtual Environment at: !VENV_PATH!
) else (
    set "PYTHON_EXE=python"
    echo [WARN] No virtual environment found. Using system 'python'.
)

:: Ensure Frontend Dependencies are Installed
if not exist "%~dp0frontend\node_modules\" (
    echo [INFO] Frontend 'node_modules' not found. Installing dependencies...
    cd /d "%~dp0frontend" && npm install
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to install frontend dependencies.
        pause
        exit /b !errorlevel!
    )
    echo [OK] Frontend dependencies installed successfully.
)

echo.
echo Starting backend server...
start "Idea Tracker - Backend Server" cmd /k "cd /d %~dp0 && "!PYTHON_EXE!" -m backend.api"

echo Starting frontend server...
start "Idea Tracker - Frontend Server" cmd /k "cd /d %~dp0frontend && npm run dev"

echo Waiting for servers to initialize...
timeout /t 5 /nobreak >nul

echo Opening browser...
start http://localhost:8080/yugas

echo.
echo =========================================================
echo  SERVERS ARE RUNNING SUCCESSFULY
echo =========================================================
echo  Backend:  http://localhost:5000
echo  Frontend: http://localhost:8080
echo  Yugas:    http://localhost:8080/yugas
echo =========================================================
echo.
echo  [!] Do not close this window unless you want to stop the servers.
echo.
echo Press any key to STOP all servers and exit...
pause >nul

echo.
echo Stopping servers...
taskkill /FI "WindowTitle eq Idea Tracker - Backend Server*" /T /F >nul 2>&1
taskkill /FI "WindowTitle eq Idea Tracker - Frontend Server*" /T /F >nul 2>&1
taskkill /FI "WindowTitle eq Backend Server*" /T /F >nul 2>&1
taskkill /FI "WindowTitle eq Frontend Server*" /T /F >nul 2>&1

:: Also release ports to ensure no orphaned processes remain
for /f "tokens=5" %%a in ('netstat -aon ^| findstr /r /c:":5000 *LISTENING"') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr /r /c:":8080 *LISTENING"') do taskkill /F /PID %%a >nul 2>&1

echo [OK] All servers stopped.
timeout /t 2 /nobreak >nul
exit

