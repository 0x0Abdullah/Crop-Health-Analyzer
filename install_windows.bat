@echo off
setlocal
cd /d "%~dp0"

echo ================================================
echo Crop Health Analyzer - Windows Setup
echo ================================================

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    py -3.12 -m venv .venv
    if errorlevel 1 (
        echo Failed to create the virtual environment. Make sure Python 3.12 is installed.
        pause
        exit /b 1
    )
)

call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
if errorlevel 1 goto :error
python -m pip install -r requirements.txt
if errorlevel 1 goto :error

echo.
echo Setup complete. Open run_windows.bat to start the application.
pause
exit /b 0

:error
echo.
echo Installation failed. Review the error above.
pause
exit /b 1
