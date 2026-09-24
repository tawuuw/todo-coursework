@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Python environment not found. Keep the project folder in its original location.
    echo See README.md for setup instructions.
    pause
    exit /b 1
)
echo ToDo: http://127.0.0.1:8001/
echo Admin: http://127.0.0.1:8001/admin/
echo Keep this window open. Press Ctrl+C to stop the server.
".venv\Scripts\python.exe" manage.py runserver 127.0.0.1:8001 --noreload
pause
