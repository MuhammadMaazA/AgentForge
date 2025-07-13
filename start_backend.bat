@echo off
echo Starting AgentForge Backend...
cd /d "c:\Users\mmaaz\Internships\Projects\AgentForge\backend"
call conda activate agentforge
echo Backend starting on http://127.0.0.1:8000
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
pause
