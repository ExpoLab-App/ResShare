import PyPDF2
from docx import Document
from io import BytesIO
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_text_from_file(file_content: bytes, filename: str) -> str:
    """
    Extract text from various file formats
    
    Args:
        file_content: Raw bytes of the file
        filename: Name of the file (used to determine format)
        
    Returns:
        Extracted text content
    """
    file_extension = filename.lower().split('.')[-1]
    
    try:
        if file_extension == 'pdf':
            return _extract_from_pdf(file_content)
        elif file_extension == 'docx':
            return _extract_from_docx(file_content)
        elif file_extension == 'txt':
            return _extract_from_txt(file_content)
        else:
            logger.warning(f"Unsupported file type: {file_extension}")
            return ""
    except Exception as e:
        logger.error(f"Failed to extract text from {filename}: {e}")
        return ""

def _extract_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF file"""
    text = ""
    try:
        pdf_reader = PyPDF2.PdfReader(BytesIO(file_content))
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
    except Exception as e:
        logger.error(f"PDF extraction error: {e}")
    return text.strip()

def _extract_from_docx(file_content: bytes) -> str:
    """Extract text from DOCX file"""
    text = ""
    try:
        doc = Document(BytesIO(file_content))
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
    except Exception as e:
        logger.error(f"DOCX extraction error: {e}")
    return text.strip()

def _extract_from_txt(file_content: bytes) -> str:
    """Extract text from TXT file"""
    try:
        return file_content.decode('utf-8', errors='ignore')
    except Exception as e:
        logger.error(f"TXT extraction error: {e}")
        return ""