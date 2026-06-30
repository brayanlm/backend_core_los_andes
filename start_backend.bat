@echo off
cd /d "D:\DAM\app_banco_los_andes\backend_core_los_andes"
.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8010
pause
