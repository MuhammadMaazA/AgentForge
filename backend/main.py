from fastapi import FastAPI
from pydantic import BaseModel
import os

app = FastAPI(title="AgentForge API")

class Prompt(BaseModel):
    text: str

@app.post("/generate")
async def generate(prompt: Prompt):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"error": "OPENAI_API_KEY not configured"}
    # TODO: integrate OpenAI API call here
    return {"message": f"Received: {prompt.text}"}

@app.get("/")
async def read_root():
    return {"message": "AgentForge backend running"}
