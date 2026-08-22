"""Fail-closed inspection helpers for untrusted uploaded documents."""

from __future__ import annotations

import io
import zipfile
from dataclasses import dataclass
from pathlib import PurePosixPath

_MAX_ZIP_ENTRIES = 1000
_MAX_ZIP_UNCOMPRESSED_BYTES = 64 * 1024 * 1024
_MAX_ZIP_MEMBER_BYTES = 32 * 1024 * 1024
_MAX_ZIP_COMPRESSION_RATIO = 200.0
_GENERIC_MIMES = frozenset({"", "application/octet-stream"})


class DocumentSecurityError(ValueError):
    """Safe, non-PHI rejection reason for an untrusted document."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class DocumentInspection:
    kind: str
    mime_type: str


_TYPE_RULES = {
    "pdf": ({"pdf"}, "application/pdf"),
    "jpeg": ({"jpg", "jpeg"}, "image/jpeg"),
    "png": ({"png"}, "image/png"),
    "webp": ({"webp"}, "image/webp"),
    "heic": ({"heic", "heif"}, "image/heic"),
    "tiff": ({"tif", "tiff"}, "image/tiff"),
    "bmp": ({"bmp"}, "image/bmp"),
    "docx": ({"docx"}, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    "xlsx": ({"xlsx"}, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    "xls": ({"xls"}, "application/vnd.ms-excel"),
    "csv": ({"csv"}, "text/csv"),
}

_MIME_KINDS = {
    "application/pdf": {"pdf"},
    "image/jpeg": {"jpeg"},
    "image/jpg": {"jpeg"},
    "image/png": {"png"},
    "image/webp": {"webp"},
    "image/heic": {"heic"},
    "image/heif": {"heic"},
    "image/tiff": {"tiff"},
    "image/bmp": {"bmp"},
    "text/csv": {"csv"},
    "application/vnd.ms-excel": {"xls", "csv"},
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {"xlsx"},
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": {"docx"},
    "application/zip": {"docx", "xlsx"},
    "application/x-zip-compressed": {"docx", "xlsx"},
}

_HEIF_BRANDS = frozenset({b"heic", b"heix", b"hevc", b"hevx", b"heif", b"mif1", b"msf1"})
_CFB_MAGIC = bytes.fromhex("D0CF11E0A1B11AE1")


def inspect_document(file_bytes: bytes, filename: str, declared_mime: str | None) -> DocumentInspection:
    """Detect content from bytes and reject extension/MIME contradictions."""
    if not file_bytes:
        raise DocumentSecurityError("empty_document")

    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    kind = _detect_kind(file_bytes, ext)
    allowed_exts, canonical_mime = _TYPE_RULES[kind]

    if ext and ext not in allowed_exts:
        raise DocumentSecurityError("extension_content_mismatch")

    mime = (declared_mime or "").split(";", 1)[0].strip().lower()
    if mime not in _GENERIC_MIMES:
        allowed_kinds = _MIME_KINDS.get(mime)
        if allowed_kinds is None or kind not in allowed_kinds:
            raise DocumentSecurityError("mime_content_mismatch")

    return DocumentInspection(kind=kind, mime_type=canonical_mime)


def validate_office_container(file_bytes: bytes, expected_kind: str) -> None:
    """Re-check an Office ZIP before any library is allowed to decompress it."""
    kind = _inspect_zip_kind(file_bytes)
    if kind != expected_kind:
        raise DocumentSecurityError("office_container_mismatch")


def _detect_kind(file_bytes: bytes, ext: str) -> str:
    head = file_bytes[:64]
    if head.startswith(b"%PDF-"):
        return "pdf"
    if head.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if len(head) >= 12 and head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "webp"
    if head.startswith((b"II*\x00", b"MM\x00*")):
        return "tiff"
    if head.startswith(b"BM"):
        return "bmp"
    if _looks_like_heif(head):
        return "heic"
    if head.startswith(b"PK\x03\x04"):
        return _inspect_zip_kind(file_bytes)
    if head.startswith(_CFB_MAGIC):
        return "xls"
    if ext == "csv" and _looks_like_csv(file_bytes):
        return "csv"
    raise DocumentSecurityError("unsupported_document_content")


def _looks_like_heif(head: bytes) -> bool:
    if len(head) < 12 or head[4:8] != b"ftyp":
        return False
    brands = {head[8:12]}
    brands.update(head[index:index + 4] for index in range(16, len(head) - 3, 4))
    return bool(brands & _HEIF_BRANDS)


def _looks_like_csv(file_bytes: bytes) -> bool:
    sample = file_bytes[:65536]
    if b"\x00" in sample:
        return False
    try:
        text = sample.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = sample.decode("latin-1")
    if "\n" not in text and "\r" not in text:
        return False
    if not any(delimiter in text for delimiter in (",", ";", "\t")):
        return False
    visible = sum(char.isprintable() or char in "\r\n\t" for char in text)
    return bool(text) and visible / len(text) >= 0.90


def _inspect_zip_kind(file_bytes: bytes) -> str:
    try:
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as archive:
            infos = archive.infolist()
            if not infos or len(infos) > _MAX_ZIP_ENTRIES:
                raise DocumentSecurityError("zip_entry_limit")

            total_uncompressed = 0
            total_compressed = 0
            names: set[str] = set()
            for info in infos:
                normalized_name = info.filename.replace("\\", "/")
                path = PurePosixPath(normalized_name)
                if path.is_absolute() or ".." in path.parts:
                    raise DocumentSecurityError("unsafe_zip_path")
                if info.flag_bits & 0x1:
                    raise DocumentSecurityError("encrypted_zip_entry")
                if info.file_size > _MAX_ZIP_MEMBER_BYTES:
                    raise DocumentSecurityError("zip_member_too_large")
                total_uncompressed += info.file_size
                total_compressed += max(info.compress_size, 1)
                if total_uncompressed > _MAX_ZIP_UNCOMPRESSED_BYTES:
                    raise DocumentSecurityError("zip_uncompressed_limit")
                names.add(normalized_name)

            if total_uncompressed / max(total_compressed, 1) > _MAX_ZIP_COMPRESSION_RATIO:
                raise DocumentSecurityError("zip_compression_ratio")

            if "[Content_Types].xml" not in names:
                raise DocumentSecurityError("unsupported_zip_container")
            if any(name.startswith("word/") for name in names):
                return "docx"
            if any(name.startswith("xl/") for name in names):
                return "xlsx"
            raise DocumentSecurityError("unsupported_zip_container")
    except DocumentSecurityError:
        raise
    except zipfile.BadZipFile as exc:
        raise DocumentSecurityError("invalid_zip_container") from exc
