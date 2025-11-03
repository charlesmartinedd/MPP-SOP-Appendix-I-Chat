from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from backend.routes import api
import uvicorn
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MPP SOP & Appendix I Chat",
    description="DoD Mentor-Protégé Program Expert Assistant powered by Grok 4",
    version="1.0.0"
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
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# Include API routes
app.include_router(api.router, prefix="/api")


@app.get("/")
async def read_root():
    """Serve the main HTML page"""
    return FileResponse("frontend/index.html")


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")

    logger.info("=" * 80)
    logger.info("MPP SOP & Appendix I Chat - Starting Server")
    logger.info("=" * 80)
    logger.info(f"Server: http://localhost:{port}")
    logger.info("Knowledge Base: MPP SOP, Appendix I, eLearning SOP")
    logger.info("LLM: Grok 4 (via OpenRouter)")
    logger.info("Embeddings: sentence-transformers/all-MiniLM-L6-v2")
    logger.info("=" * 80)

    uvicorn.run(app, host=host, port=port)
