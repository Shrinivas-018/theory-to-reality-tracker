@echo off
title Idea Evolution Tracker Stopper
echo =========================================================
echo  STOPPING THEORY-TO-REALITY EVOLUTION TRACKER SERVERS
echo =========================================================
echo.

echo [1/2] Terminating terminal windows...
taskkill /FI "WindowTitle eq Idea Tracker - Backend Server*" /T /F >nul 2>&1
taskkill /FI "WindowTitle eq Idea Tracker - Frontend Server*" /T /F >nul 2>&1
taskkill /FI "WindowTitle eq Backend Server*" /T /F >nul 2>&1
taskkill /FI "WindowTitle eq Frontend Server*" /T /F >nul 2>&1

echo [2/2] Releasing ports (5000 and 8080)...
:: Find and kill process listening on port 5000 (Flask Backend)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr /r /c:":5000 *LISTENING"') do (
    echo Terminating backend PID %%a on port 5000...
    taskkill /F /PID %%a >nul 2>&1
)

:: Find and kill process listening on port 8080 (Vite Frontend)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr /r /c:":8080 *LISTENING"') do (
    echo Terminating frontend PID %%a on port 8080...
    taskkill /F /PID %%a >nul 2>&1
)

echo.
echo =========================================================
echo  All servers stopped successfully.
echo =========================================================
echo.
timeout /t 3 /nobreak >nul
exit

