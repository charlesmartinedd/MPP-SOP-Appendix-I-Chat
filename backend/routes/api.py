from fastapi import APIRouter, HTTPException
from backend.models.schemas import ChatMessage, ChatResponse, HealthResponse
from backend.services.chat_service import ChatService
from backend.services.rag_service import RAGService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services
chat_service = ChatService()
rag_service = RAGService()


@router.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """Handle chat requests with optional RAG context"""
    try:
        sources = None

        # Get RAG context if enabled
        if message.use_rag:
            sources = rag_service.query(message.message, n_results=5)
            logger.info(f"Retrieved {len(sources)} relevant sources")

        # Generate response with Grok 4
        response = chat_service.generate_response(message.message, context=sources)

        return ChatResponse(response=response, sources=sources)

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint"""
    try:
        doc_count = rag_service.get_document_count()
        return HealthResponse(
            status="healthy",
            document_count=doc_count,
            model=chat_service.model,
            collection=rag_service.collection_name
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/count")
async def get_document_count():
    """Get the number of document chunks"""
    try:
        count = rag_service.get_document_count()
        return {"count": count}
    except Exception as e:
        logger.error(f"Error getting document count: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
