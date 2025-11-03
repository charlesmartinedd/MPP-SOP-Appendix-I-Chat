"""
One-time initialization script to load MPP documents into ChromaDB
Run this before starting the server for the first time:
    python init_documents.py
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.insert(0, os.path.abspath('.'))

from backend.services.rag_service import RAGService
from backend.services.document_processor import DocumentProcessor
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    logger.info("=" * 80)
    logger.info("MPP Knowledge Base Initialization")
    logger.info("=" * 80)

    # Check if documents directory exists
    documents_dir = "documents"
    if not os.path.exists(documents_dir):
        logger.error(f"Documents directory not found: {documents_dir}")
        logger.error("Please create the 'documents/' folder and add your MPP documents")
        sys.exit(1)

    # Check for required documents
    required_docs = ["MPP SOP.pdf", "Appendix I.pdf", "SOP for eLearning Products.docx"]
    missing_docs = []

    for doc in required_docs:
        if not os.path.exists(os.path.join(documents_dir, doc)):
            missing_docs.append(doc)

    if missing_docs:
        logger.warning(f"Missing documents: {', '.join(missing_docs)}")
        logger.warning("Continuing with available documents...")

    # Initialize RAG service
    logger.info("Initializing RAG service...")
    rag = RAGService()

    # Check if already initialized
    current_count = rag.get_document_count()
    if current_count > 0:
        logger.warning(f"Database already contains {current_count} chunks")
        response = input("Do you want to clear and reinitialize? (yes/no): ")
        if response.lower() == 'yes':
            logger.info("Clearing existing database...")
            rag.clear_collection()
        else:
            logger.info("Keeping existing database. Exiting.")
            sys.exit(0)

    # Process all documents
    logger.info(f"Processing documents from: {documents_dir}")
    documents = DocumentProcessor.process_all_documents(documents_dir)

    if not documents:
        logger.error("No documents were processed!")
        sys.exit(1)

    # Add to RAG system
    logger.info("Adding documents to ChromaDB...")
    total_chunks = 0
    for doc in documents:
        logger.info(f"Processing: {doc['filename']} ({len(doc['text'])} characters)")
        chunks = rag.add_document(doc['text'], doc['filename'])
        total_chunks += chunks
        logger.info(f"  → Added {chunks} chunks")

    logger.info("=" * 80)
    logger.info("✅ Initialization Complete!")
    logger.info("=" * 80)
    logger.info(f"Documents loaded: {len(documents)}")
    logger.info(f"Total chunks: {total_chunks}")
    logger.info("\nDocuments in knowledge base:")
    for doc in documents:
        logger.info(f"  • {doc['filename']}")
    logger.info("=" * 80)
    logger.info("\nNext step: Run the server with 'python run.py'")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nInitialization cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error during initialization: {str(e)}", exc_info=True)
        sys.exit(1)
