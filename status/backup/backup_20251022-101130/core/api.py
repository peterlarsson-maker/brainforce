from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import os
import requests

router = APIRouter()

class OpenAIRequest(BaseModel):
    prompt: str
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: int = 512

@router.post("/openai/")
def openai_proxy(req: OpenAIRequest):
    if os.getenv("MOCK_MODE") == "1":
        return {"response": f"MOCK: {req.prompt[:32]} ..."}
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=403, detail="Ingen API-nyckel satt")
    resp = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": req.model,
            "messages": [{"role": "user", "content": req.prompt}],
            "temperature": req.temperature,
            "max_tokens": req.max_tokens
        }
    )
    return resp.json()
