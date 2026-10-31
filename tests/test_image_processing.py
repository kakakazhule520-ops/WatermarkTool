@echo off
setlocal
cd /d "%~dp0.."
python -m pip install -r requirements.txt
pyinstaller --noconsole --onedir --name WatermarkTool main.py
if errorlevel 1 (
    echo Build failed.
    exit /b 1
)
echo Build complete.
