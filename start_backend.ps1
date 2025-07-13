#!/usr/bin/env pwsh
cd "c:\Users\mmaaz\Internships\Projects\AgentForge\backend"
conda activate agentforge
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
