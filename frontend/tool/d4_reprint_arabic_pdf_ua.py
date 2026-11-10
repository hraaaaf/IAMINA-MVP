#!/usr/bin/env python3
"""Strictly synthetic Arabic tagged PDF proof. NOT a patient export API."""
from pathlib import Path
from urllib.parse import unquote, urlsplit

from weasyprint import HTML, default_url_fetcher

PROOF_DIR = Path("build/d4-synthetic-proof").resolve()
FONT = Path("/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf").resolve()
ASSETS = Path("assets/fonts").resolve()


def offline_font_only(url, *args, **kwargs):
    parts = urlsplit(url)
    if parts.scheme != "file" or parts.netloc not in ("", "localhost"):
        raise ValueError("CAL-12: network asset prohibited in synthetic PDF")
    path = Path(unquote(parts.path)).resolve()
    if path not in (FONT, ASSETS / "Inter.ttf", ASSETS / "NotoSansArabic.ttf"):
        raise ValueError("CAL-12: unexpected local PDF asset")
    if not path.is_file():
        raise FileNotFoundError(path)
    return default_url_fetcher(url, *args, **kwargs)


def main():
    if not FONT.is_file():
        raise FileNotFoundError("Local Noto Naskh Arabic font required")
    for name in ("Inter.ttf", "NotoSansArabic.ttf"):
        if not (ASSETS / name).is_file():
            raise FileNotFoundError(f"Missing bundled font: {name}")
    for suffix in ("", "-MAX"):
        name = f"D4-SYNTHETIC{suffix}-ar"
        html_file = PROOF_DIR / f"{name}.html"
        pdf_file = PROOF_DIR / f"{name}.pdf"
        source = html_file.read_text(encoding="utf-8")
        if source.count("</style>") != 1 or '<html lang="ar" dir="rtl">' not in source:
            raise ValueError("Unexpected Arabic HTML fixture")
        if "بيانات تجريبية فقط - غير صالحة للاستخدام الطبي" not in source:
            raise ValueError("Missing synthetic, non-clinical warning")
        local_style = (
            '@font-face{font-family:D4Naskh;src:url("'
            + FONT.as_uri()
            + '") format("truetype")}'
            'html[dir="rtl"] body{font-family:D4Naskh,Inter,sans-serif !important}'
        )
        source = source.replace("</style>", local_style + "</style>")
        HTML(
            string=source,
            base_url=html_file.as_uri(),
            url_fetcher=offline_font_only,
        ).write_pdf(target=str(pdf_file), pdf_variant="pdf/ua-1")
        if pdf_file.stat().st_size < 3000:
            raise RuntimeError("Empty Arabic synthetic PDF")
        print("CAL12_ARABIC_TEXT_CANDIDATE", pdf_file.name, pdf_file.stat().st_size)


if __name__ == "__main__":
    main()
