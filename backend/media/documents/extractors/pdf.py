"""Bounded digital-PDF extractor for the Document Pulper.

Scanned/image-only medical PDFs fail closed until a qualified document OCR
runtime is available. Tesseract is intentionally not used for biomarker OCR.
"""

from __future__ import annotations

import io
import logging
from typing import Tuple

from media.documents.security import DocumentSecurityError

logger = logging.getLogger(__name__)

_MAX_PDF_PAGES = 50
_MAX_TEXT_CHARS = 1_000_000


def extract_pdf(file_bytes: bytes) -> Tuple[str, bool]:
    """Extract bounded text from a digital PDF or reject an unqualified scan."""
    text = _try_pdfplumber(file_bytes)
    if text and len(text.strip()) > 50:
        return text, False

    raise DocumentSecurityError("pdf_scanned_ocr_unqualified")


def _append_bounded(parts: list[str], text: str, total_chars: int) -> int:
    total_chars += len(text)
    if total_chars > _MAX_TEXT_CHARS:
        raise DocumentSecurityError("pdf_text_limit")
    parts.append(text)
    return total_chars


def _try_pdfplumber(file_bytes: bytes) -> str:
    try:
        import pdfplumber

        texts: list[str] = []
        total_chars = 0
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            if len(pdf.pages) > _MAX_PDF_PAGES:
                raise DocumentSecurityError("pdf_page_limit")
            for page in pdf.pages:
                total_chars = _append_bounded(
                    texts,
                    page.extract_text() or "",
                    total_chars,
                )
                for table in page.extract_tables():
                    for row in table:
                        total_chars = _append_bounded(
                            texts,
                            "\t".join(cell or "" for cell in row),
                            total_chars,
                        )
        return "\n".join(texts)
    except DocumentSecurityError:
        raise
    except ImportError:
        logger.warning("pdf_extractor: pdfplumber unavailable")
        return ""
    except Exception as exc:
        logger.warning(
            "pdf_extractor: pdfplumber failed error_class=%s",
            type(exc).__name__,
        )
        return ""
