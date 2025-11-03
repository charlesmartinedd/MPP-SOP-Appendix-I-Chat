import os
import pypdf
from docx import Document
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Process PDFs and DOCX files for the MPP knowledge base"""

    @staticmethod
    def extract_pdf(file_path: str) -> str:
        """Extract text from PDF with page tracking"""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                for page_num, page in enumerate(pdf_reader.pages, start=1):
                    page_text = page.extract_text()
                    text += f"\n[Page {page_num}]\n{page_text}"
            logger.info(f"Extracted {len(pdf_reader.pages)} pages from PDF: {os.path.basename(file_path)}")
        except Exception as e:
            logger.error(f"Error extracting PDF {file_path}: {str(e)}")
        return text

    @staticmethod
    def extract_docx(file_path: str) -> str:
        """Extract text from DOCX"""
        text = ""
        try:
            doc = Document(file_path)
            paragraphs = [paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip()]
            text = "\n".join(paragraphs)
            logger.info(f"Extracted {len(paragraphs)} paragraphs from DOCX: {os.path.basename(file_path)}")
        except Exception as e:
            logger.error(f"Error extracting DOCX {file_path}: {str(e)}")
        return text

    @staticmethod
    def process_all_documents(documents_dir: str) -> List[Dict]:
        """Process all documents in the directory"""
        processed = []

        if not os.path.exists(documents_dir):
            logger.error(f"Documents directory not found: {documents_dir}")
            return processed

        files = os.listdir(documents_dir)
        logger.info(f"Found {len(files)} files in {documents_dir}")

        for filename in files:
            file_path = os.path.join(documents_dir, filename)

            if not os.path.isfile(file_path):
                continue

            try:
                if filename.endswith('.pdf'):
                    text = DocumentProcessor.extract_pdf(file_path)
                    if text:
                        processed.append({"filename": filename, "text": text})
                        logger.info(f"✓ Processed PDF: {filename} ({len(text)} chars)")

                elif filename.endswith('.docx'):
                    text = DocumentProcessor.extract_docx(file_path)
                    if text:
                        processed.append({"filename": filename, "text": text})
                        logger.info(f"✓ Processed DOCX: {filename} ({len(text)} chars)")

            except Exception as e:
                logger.error(f"✗ Error processing {filename}: {str(e)}")

        return processed
