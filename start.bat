@echo off
rem Starts the ContextShield backend and frontend in two windows.
cd /d "%~dp0"
start "ContextShield backend" cmd /k "cd backend && .venv\Scripts\python -m uvicorn app.main:app --port 8000"
start "ContextShield frontend" cmd /k "cd frontend && npm run dev"
echo Backend:  http://localhost:8000/docs
echo Frontend: http://localhost:3000
