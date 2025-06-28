from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
import openai
import os

load_dotenv()

app = FastAPI(title="AgentForge API")

class Prompt(BaseModel):
    text: str

@app.post("/generate")
async def generate(prompt: Prompt):
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    if not api_key:
        return {"error": "OPENAI_API_KEY not configured"}

    openai.api_key = api_key

    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": prompt.text}],
            max_tokens=50,
        )
        content = response.choices[0].message.content
        return {"message": content}
    except Exception as e:
        return {"error": str(e)}

@app.get("/")
async def read_root():
    return {"message": "AgentForge backend running"}
