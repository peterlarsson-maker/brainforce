from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core import api, memory, logger, mock
import os

app = FastAPI(
    title="BrainForce API",
    description="OpenAI-kompatibel backend med minne, licens och loggning",
    version="3.0.0"
)

app.include_router(api.router, prefix="/api")
app.include_router(memory.router, prefix="/memory")
app.include_router(logger.router, prefix="/logs")
app.include_router(mock.router, prefix="/mock")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Anpassa vid deployment!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"msg": "BrainForce backend API running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
