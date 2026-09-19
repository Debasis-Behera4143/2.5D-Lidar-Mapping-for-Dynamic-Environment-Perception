@echo off
echo ============================================================
echo Setting up LiDAR Adaptive Mapping environment with Python 3.11
echo ============================================================

set UV_PATH=C:\Users\debas\AppData\Local\hermes\bin\uv.exe

if not exist "%UV_PATH%" (
    where uv >nul 2>nul
    if %ERRORLEVEL% equ 0 (
        set UV_PATH=uv
    ) else (
        echo [ERROR] uv is not installed or not found.
        exit /b 1
    )
)

echo Creating .venv with Python 3.11...
"%UV_PATH%" venv .venv --python 3.11
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to create virtual environment.
    exit /b %ERRORLEVEL%
)

echo Installing dependencies...
"%UV_PATH%" pip install -r requirements.txt --python .venv\Scripts\python.exe
"%UV_PATH%" pip install open3d --python .venv\Scripts\python.exe

echo.
echo ============================================================
echo Setup complete! To activate:
echo .venv\Scripts\activate.bat
echo ============================================================
