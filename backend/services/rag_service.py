import os
import chromadb
from typing import List, Dict
from sentence_transformers import SentenceTransformer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGService:
    """Service for managing RAG (Retrieval-Augmented Generation)"""

    def __init__(self):
        self.collection_name = os.getenv("COLLECTION_NAME", "mpp_documents")
        self.embedding_model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        self.chunk_size = int(os.getenv("CHUNK_SIZE", "1000"))
        self.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "200"))

        # Initialize ChromaDB (new API)
        self.client = chromadb.PersistentClient(path="./chroma_db")

        # Initialize embedding model (same as Government Expert)
        logger.info(f"Loading embedding model: {self.embedding_model_name}")
        self.embedding_model = SentenceTransformer(self.embedding_model_name)

        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=self.collection_name)
            logger.info(f"Loaded existing collection: {self.collection_name}")
        except:
            self.collection = self.client.create_collection(name=self.collection_name)
            logger.info(f"Created new collection: {self.collection_name}")

    def chunk_text(self, text: str) -> List[str]:
        """Split text into chunks with overlap"""
        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + self.chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start += self.chunk_size - self.chunk_overlap

        return chunks

    def add_document(self, text: str, filename: str) -> int:
        """Add a document to the RAG system"""
        chunks = self.chunk_text(text)

        # Create embeddings
        embeddings = self.embedding_model.encode(chunks).tolist()

        # Generate unique IDs
        doc_count = self.collection.count()
        ids = [f"{filename}_{doc_count}_{i}" for i in range(len(chunks))]

        # Add to collection
        self.collection.add(
            embeddings=embeddings,
            documents=chunks,
            metadatas=[{"source": filename, "chunk": i} for i in range(len(chunks))],
            ids=ids
        )

        logger.info(f"Added {len(chunks)} chunks from {filename}")
        return len(chunks)

    def query(self, query_text: str, n_results: int = 5) -> List[Dict]:
        """Query the RAG system for relevant documents"""
        # Create query embedding
        query_embedding = self.embedding_model.encode([query_text]).tolist()

        # Query the collection
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=n_results
        )

        # Format results
        sources = []
        if results['documents'] and len(results['documents']) > 0:
            for i, doc in enumerate(results['documents'][0]):
                sources.append({
                    "text": doc,
                    "source": results['metadatas'][0][i].get('source', 'unknown'),
                    "chunk": results['metadatas'][0][i].get('chunk', 0),
                    "distance": results['distances'][0][i] if 'distances' in results else None
                })

        return sources

    def get_document_count(self) -> int:
        """Get the number of document chunks in the collection"""
        return self.collection.count()

    def clear_collection(self):
        """Clear all documents from the collection"""
        self.client.delete_collection(name=self.collection_name)
        self.collection = self.client.create_collection(name=self.collection_name)
        logger.info(f"Cleared collection: {self.collection_name}")
