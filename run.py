"""
Main startup script for MPP SOP & Appendix I Chat
Usage: python run.py
"""
import uvicorn
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.insert(0, os.path.abspath('.'))

from backend.main import app
from backend.services.rag_service import RAGService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_initialization():
    """Check if documents are loaded"""
    try:
        rag = RAGService()
        count = rag.get_document_count()
        if count == 0:
            logger.warning("=" * 80)
            logger.warning("WARNING: No documents loaded in the knowledge base!")
            logger.warning("=" * 80)
            logger.warning("Please run: python init_documents.py")
            logger.warning("This will load the MPP documents into ChromaDB")
            logger.warning("=" * 80)
            response = input("\nContinue anyway? (yes/no): ")
            if response.lower() != 'yes':
                sys.exit(0)
        else:
            logger.info(f"Knowledge base loaded: {count} document chunks")
    except Exception as e:
        logger.error(f"Error checking initialization: {str(e)}")


if __name__ == "__main__":
    # Check environment
    if not os.getenv("OPENROUTER_API_KEY"):
        logger.error("=" * 80)
        logger.error("ERROR: OPENROUTER_API_KEY not found!")
        logger.error("=" * 80)
        logger.error("Please create a .env file with your OpenRouter API key:")
        logger.error("  OPENROUTER_API_KEY=your-key-here")
        logger.error("=" * 80)
        sys.exit(1)

    # Check if documents are loaded
    check_initialization()

    # Start server
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")

    print("\n" + "=" * 80)
    print("MPP SOP & Appendix I Chat")
    print("=" * 80)
    print(f"Server URL: http://localhost:{port}")
    print("Knowledge Base: MPP SOP, Appendix I, eLearning SOP")
    print("LLM: Grok 4 (via OpenRouter)")
    print("Embeddings: sentence-transformers/all-MiniLM-L6-v2")
    print("=" * 80)
    print("\nPress Ctrl+C to stop the server\n")

    try:
        uvicorn.run(app, host=host, port=port, log_level="info")
    except KeyboardInterrupt:
        print("\n\n" + "=" * 80)
        print("Server stopped")
        print("=" * 80)
