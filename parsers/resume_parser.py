import io

try:
    from pypdf import PdfReader
    PDF_AVAILABLE = True
except ImportError:
    PdfReader = None
    PDF_AVAILABLE = False

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    Document = None
    DOCX_AVAILABLE = False


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
        if not PDF_AVAILABLE:
            return "PDF parsing is unavailable because pypdf is not installed. Upload a TXT resume or install pypdf."
        try:
            reader = PdfReader(io.BytesIO(file_bytes))
            pages = [page.extract_text() or "" for page in reader.pages]
            return "\n\n".join(pages).strip()
        except Exception:
            return "Unable to extract text from PDF resume."

    def _parse_docx(self, file_bytes: bytes) -> str:
        if not DOCX_AVAILABLE:
            return "DOCX parsing is unavailable because python-docx is not installed. Upload a TXT resume or install python-docx."
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
