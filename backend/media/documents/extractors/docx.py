"""
DOCX / plain-text extractor — Phase 12 Document Pulper.

Extracts all paragraph and table text from .docx files.
Returns raw text that is then passed to the LLM parsing prompt.
"""
from __future__ import annotations

import io
import logging

logger = logging.getLogger(__name__)


def extract_docx(file_bytes: bytes) -> str:
    """
    Extract text from a Word (.docx) file.

    Returns plain text, or '' on failure.
    """
    try:
        from docx import Document
        doc    = Document(io.BytesIO(file_bytes))
        parts  = []

        # Paragraphs
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                parts.append(text)

        # Tables
        for table in doc.tables:
            for row in table.rows:
                row_text = '\t'.join(cell.text.strip() for cell in row.cells)
                if row_text.strip():
                    parts.append(row_text)

        return '\n'.join(parts)

    except ImportError:
        logger.error("python-docx not installed — DOCX extraction unavailable.")
        return ''
    except Exception as exc:
        logger.warning("docx_extractor: failed: %s", exc)
        return ''
