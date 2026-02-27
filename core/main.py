from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core import api, memory, logger, mock
from core import auth
from core.database import init_db
import os

# Ensure DB schema is initialized before the app starts handling requests
init_db()

app = FastAPI(
    title="BrainForce API",
    description="OpenAI-kompatibel backend med minne, licens och loggning",
    version="3.0.0"
)

# early sanity check: JWT_SECRET must be provided or authentication cannot work
@app.on_event("startup")
def _check_jwt_secret():
    if not os.getenv("JWT_SECRET"):
        # raising here prevents the app from starting and produces a clear message
        raise RuntimeError("JWT_SECRET environment variable must be set for authentication")

app.include_router(api.router, prefix="/api")
app.include_router(memory.router, prefix="/memory")
app.include_router(logger.router, prefix="/logs")
app.include_router(mock.router, prefix="/mock")
# authentication endpoints
app.include_router(auth.router, prefix="/auth")

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
