@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Не найдено окружение Python. Не перемещайте папку проекта перед показом.
    echo Инструкция установки находится в README.md.
    pause
    exit /b 1
)
echo ToDo: http://127.0.0.1:8001/
echo Администратор: http://127.0.0.1:8001/admin/
echo Оставьте это окно открытым. Для остановки нажмите Ctrl+C.
".venv\Scripts\python.exe" manage.py runserver 127.0.0.1:8001 --noreload
pause
