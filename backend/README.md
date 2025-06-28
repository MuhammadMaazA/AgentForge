# AgentForge Backend

This FastAPI backend provides endpoints for generating code with AI.

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# add your OPENAI_API_KEY to .env
# optionally adjust OPENAI_MODEL
```

## Running

```bash
uvicorn main:app --reload
```
