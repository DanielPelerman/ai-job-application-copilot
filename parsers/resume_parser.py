import io
from pypdf import PdfReader
from docx import Document

class ResumeParser:
    """Parser for extracting text from resume files."""

    def parse(self, file_bytes: bytes, filename: str) -> str:
        lower_name = filename.lower()
        if lower_name.endswith(".pdf"):
            return self._parse_pdf(file_bytes)
        if lower_name.endswith(".docx"):
            return self._parse_docx(file_bytes)
        return self._parse_text(file_bytes)

    def _parse_pdf(self, file_bytes: bytes) -> str:
        try:
            reader = PdfReader(io.BytesIO(file_bytes))
            pages = [page.extract_text() or "" for page in reader.pages]
            return "\n\n".join(pages).strip()
        except Exception:
            return "Unable to extract text from PDF resume."

    def _parse_docx(self, file_bytes: bytes) -> str:
        try:
            document = Document(io.BytesIO(file_bytes))
            paragraphs = [paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()]
            return "\n".join(paragraphs).strip()
        except Exception:
            return "Unable to extract text from DOCX resume."

    def _parse_text(self, file_bytes: bytes) -> str:
        try:
            return file_bytes.decode("utf-8").strip()
        except Exception:
            return file_bytes.decode("latin-1", errors="ignore").strip()
