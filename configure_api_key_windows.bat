@echo off
setlocal
cd /d "%~dp0"
title Interview Assist - Update API Key
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" setup_api_key.py --replace
) else (
    where py >nul 2>nul
    if not errorlevel 1 (
        py -3 setup_api_key.py --replace
    ) else (
        python setup_api_key.py --replace
    )
)
echo.
echo Restart launch_windows.bat after updating your key.
pause
endlocal
