from io import BytesIO
import PyPDF2
from docx import Document

from mcp_server.validation import SUPPORTED_UPLOAD_EXTENSIONS, ValidationError


def extract_text(file_content: bytes, filename: str) -> str:
    extension = filename.lower().rsplit(".", maxsplit=1)[-1] if "." in filename else ""
    if extension not in SUPPORTED_UPLOAD_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_UPLOAD_EXTENSIONS))
        raise ValidationError(
            f"Unsupported file type '.{extension}'. Supported: {supported}."
        )

    if extension == "pdf":
        return _extract_from_pdf(file_content)
    if extension == "docx":
        return _extract_from_docx(file_content)
    return _extract_from_txt(file_content)


def _extract_from_pdf(file_content: bytes) -> str:

    pdf_reader = PyPDF2.PdfReader(BytesIO(file_content))
    pages = [page.extract_text() or "" for page in pdf_reader.pages]
    return "\n".join(pages).strip()


def _extract_from_docx(file_content: bytes) -> str:

    doc = Document(BytesIO(file_content))
    paragraphs = [paragraph.text for paragraph in doc.paragraphs]
    return "\n".join(paragraphs).strip()


def _extract_from_txt(file_content: bytes) -> str:
    return file_content.decode("utf-8", errors="ignore").strip()
