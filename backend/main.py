import logging
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.routes import api

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "frontend" / "static"
INDEX_FILE = BASE_DIR / "frontend" / "index.html"

app = FastAPI(
    title="MPP SOP & Appendix I Chat",
    description="DoD Mentor-Protégé Program expert assistant powered by Grok 4 and Gemini verification",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
else:
    logger.warning("Static directory not found at %s", STATIC_DIR)

# Include API routes
app.include_router(api.router, prefix="/api")


@app.get("/")
async def read_root():
    """Serve the main HTML page"""
    if not INDEX_FILE.exists():
        logger.error("Frontend index file not found at %s", INDEX_FILE)
        raise HTTPException(status_code=500, detail="Frontend build is missing.")

    return FileResponse(str(INDEX_FILE))


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")

    logger.info("=" * 80)
    logger.info("MPP SOP & Appendix I Chat - Starting Server")
    logger.info("=" * 80)
    logger.info("Server: http://%s:%s", host, port)
    logger.info("Knowledge Base: MPP SOP, Appendix I, eLearning SOP")
    logger.info("LLM: Grok 4 (xAI) + Gemini 2.5 Pro")
    logger.info("Embeddings: sentence-transformers/all-MiniLM-L6-v2")
    logger.info("=" * 80)

    import uvicorn

    uvicorn.run(app, host=host, port=port)
