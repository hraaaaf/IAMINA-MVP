"""
PDF extractor — Phase 12 Document Pulper.

Two-pass strategy:
  1. pdfplumber — extracts text from digital (text-layer) PDFs.
     Fast, no GPU, handles tables.
  2. pytesseract (OCR) — fallback for scanned / image-only PDFs.
     Requires Tesseract to be installed (apt install tesseract-ocr).
     Gracefully disabled if not available.

Returns (text: str, is_scanned: bool)
"""
from __future__ import annotations

import io
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


def extract_pdf(file_bytes: bytes) -> Tuple[str, bool]:
    """
    Extract raw text from a PDF.

    Returns:
        (text, is_scanned)
        text       — extracted string (may be empty on total failure)
        is_scanned — True when pytesseract OCR was used
    """
    # ── Pass 1: pdfplumber (text-layer PDFs) ──────────────────────────────────
    text = _try_pdfplumber(file_bytes)
    if text and len(text.strip()) > 50:
        return text, False

    # ── Pass 2: pytesseract OCR fallback ─────────────────────────────────────
    ocr_text = _try_ocr(file_bytes)
    if ocr_text:
        return ocr_text, True

    logger.warning("pdf_extractor: both pdfplumber and OCR returned empty text.")
    return text or '', False


def _try_pdfplumber(file_bytes: bytes) -> str:
    try:
        import pdfplumber  # optional dependency
        texts = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ''
                texts.append(page_text)
                # Also extract tables as tab-separated rows
                for table in page.extract_tables():
                    for row in table:
                        row_text = '\t'.join(cell or '' for cell in row)
                        texts.append(row_text)
        return '\n'.join(texts)
    except ImportError:
        logger.warning("pdfplumber not installed — PDF text extraction unavailable.")
        return ''
    except Exception as exc:
        logger.warning("pdfplumber failed: %s", exc)
        return ''


def _try_ocr(file_bytes: bytes) -> str:
    """Convert PDF pages to images and run Tesseract OCR."""
    try:
        import fitz  # PyMuPDF — for pdf→image conversion
        import pytesseract
        from PIL import Image

        doc   = fitz.open(stream=file_bytes, filetype="pdf")
        texts = []
        for page in doc:
            mat  = fitz.Matrix(2, 2)   # 2x zoom → better OCR quality
            pix  = page.get_pixmap(matrix=mat)
            img  = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            text = pytesseract.image_to_string(img, lang='fra+eng')
            texts.append(text)
        doc.close()
        return '\n'.join(texts)
    except ImportError:
        logger.info("PyMuPDF or pytesseract not installed — OCR skipped.")
        return ''
    except Exception as exc:
        logger.warning("OCR extraction failed: %s", exc)
        return ''
