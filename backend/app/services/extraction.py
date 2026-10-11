import io
import zipfile
from pathlib import PurePath

from docx import Document as DocxDocument
from docx.table import Table
from pypdf import PdfReader

from app.services.exceptions import FileTooLarge, UnreadableFile, UnsupportedFileType


class TextExtractor:
    """Turns an uploaded file into plain text. Blocking: run it with asyncio.to_thread."""

    def __init__(
        self,
        max_bytes: int,
        max_pdf_pages: int = 500,
        max_unpacked_bytes: int = 50 * 1024 * 1024,
    ) -> None:
        self._max_bytes = max_bytes
        self._max_pdf_pages = max_pdf_pages
        self._max_unpacked_bytes = max_unpacked_bytes

    def extract(self, filename: str, data: bytes) -> str:
        if len(data) > self._max_bytes:
            limit = f"{self._max_bytes / (1024 * 1024):.0f} MB"
            raise FileTooLarge(f"File is too large. The limit is {limit}.")
        if not data:
            raise UnreadableFile("The file is empty.")

        extension = PurePath(filename).suffix.lower()
        if extension in (".txt", ".md"):
            return self._read_text(data)
        if extension == ".pdf":
            return self._read_pdf(data)
        if extension == ".docx":
            return self._read_docx(data)
        raise UnsupportedFileType("Unsupported file type. Use .txt, .md, .pdf or .docx.")

    @staticmethod
    def _read_text(data: bytes) -> str:
        try:
            text = data.decode("utf-8-sig")
        except UnicodeDecodeError:
            raise UnreadableFile("Text files must be UTF-8 encoded.") from None
        if "\x00" in text:
            raise UnreadableFile("This does not look like a text file.")
        return text

    def _read_pdf(self, data: bytes) -> str:
        if not data.startswith(b"%PDF"):
            raise UnreadableFile("This file is not a valid PDF.")
        try:
            reader = PdfReader(io.BytesIO(data))
            if reader.is_encrypted:
                raise UnreadableFile("This PDF is password protected.")
            if len(reader.pages) > self._max_pdf_pages:
                raise UnreadableFile(
                    f"This PDF has more than {self._max_pdf_pages} pages."
                )
            pages = [page.extract_text() or "" for page in reader.pages]
        except UnreadableFile:
            raise
        except Exception:
            raise UnreadableFile("The PDF could not be read.") from None

        text = "\n\n".join(page.strip() for page in pages if page.strip())
        if not text:
            raise UnreadableFile("No readable text found. Scanned PDFs are not supported.")
        return text

    def _read_docx(self, data: bytes) -> str:
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                unpacked = sum(item.file_size for item in archive.infolist())
            if unpacked > self._max_unpacked_bytes:
                raise UnreadableFile("This document is too large once unpacked.")

            document = DocxDocument(io.BytesIO(data))
            parts: list[str] = []
            for block in document.iter_inner_content():
                if isinstance(block, Table):
                    for row in block.rows:
                        cells = [cell.text.strip() for cell in row.cells]
                        parts.append(" | ".join(cell for cell in cells if cell))
                else:
                    parts.append(block.text)
        except UnreadableFile:
            raise
        except Exception:
            raise UnreadableFile("The Word document could not be read.") from None

        text = "\n".join(parts).strip()
        if not text:
            raise UnreadableFile("No readable text found in this document.")
        return text