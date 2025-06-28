from fastapi import FastAPI
from pydantic import BaseModel
import os

app = FastAPI(title="AgentForge Backend")

class AgentRequest(BaseModel):
    description: str

@app.get("/")
def read_root():
    return {"message": "AgentForge backend running"}

@app.post("/generate")
def generate_agent(req: AgentRequest):
    # Placeholder for future OpenAI integration
    return {"generated_code": f"# TODO: generate code for: {req.description}"}
