from fastapi import APIRouter
router = APIRouter()

@router.get("/openai/")
def mock_openai():
    return {"response": "Detta är mock-läge. Ingen riktig OpenAI-anslutning."}
