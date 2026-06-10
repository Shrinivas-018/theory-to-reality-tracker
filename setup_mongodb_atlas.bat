@echo off
echo ========================================
echo MongoDB Atlas Setup for Yugas Evolution
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/
    pause
    exit /b 1
)

REM Run the setup script
python setup_mongodb_atlas.py

if errorlevel 1 (
    echo.
    echo Setup failed. Please check the errors above.
    pause
    exit /b 1
)

echo.
echo Setup completed successfully!
echo You can now start the application with: start.bat
echo.
pause
