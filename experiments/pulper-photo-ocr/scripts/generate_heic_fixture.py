"""Create a synthetic HEIC fixture from the generated FR clean PNG.
No patient image and no network calls. Uses Pillow/Libheif for an actual HEIF file.
"""
from pathlib import Path
from PIL import Image
from pillow_heif import register_heif_opener

root = Path("public/fixtures")
source = root / "fr_clean.png"
target = root / "fr_clean.heic"
if not source.exists():
    raise SystemExit("Run npm run fixtures before HEIC encoding")
register_heif_opener()
with Image.open(source) as image:
    image.convert("RGB").save(target, format="HEIF", quality=95)
data = target.read_bytes()
if len(data) < 100 or data[4:8] != b"ftyp" or data[8:12] not in {
    b"heic", b"heix", b"hevc", b"hevx", b"mif1"
}:
    raise SystemExit("HEIC output does not have an expected HEIF signature")
print(f"Generated synthetic HEIC fixture: {target.name} ({len(data)} bytes)")
