@echo off
echo Starting Theory-to-Reality Evolution Tracker...
echo.

echo [1/2] Starting Flask Backend on http://localhost:5000
start "Backend" cmd /k "python -m backend.api"

echo [2/2] Starting React Frontend on http://localhost:8080
start "Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo Both servers are starting...
echo Backend:  http://localhost:5000
echo Frontend: http://localhost:8080
echo.
echo Close the two terminal windows to stop the servers.
pause
