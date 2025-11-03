from pydantic import BaseModel
from typing import List, Optional


class ChatMessage(BaseModel):
    """Chat message request"""
    message: str
    use_rag: bool = True


class ChatResponse(BaseModel):
    """Chat response with sources"""
    response: str
    sources: Optional[List[dict]] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    document_count: int
    model: str
    collection: str
