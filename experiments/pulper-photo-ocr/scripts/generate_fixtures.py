"""Synthetic-only medical OCR images. Never use patient material."""
import argparse
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

CASES = (
    dict(id="fr_clean",language="fr",format="PNG",lines=["GLYCEMIE 108 mg/dL","HbA1c 6.7 %"],expectedNumbers=["108","6.7"],expectedUnits=["mg/dl","%"],expectedLabels=["GLYCEMIE","HbA1c"]),
    dict(id="fr_decimal_rotate",language="fr",format="PNG",lines=["Glucose 7,4 mmol/L","2026-10-15"],expectedNumbers=["7.4","2026","10","15"],expectedUnits=["mmol/l"],expectedLabels=["Glucose"],rotate=3.0),
    dict(id="fr_contrast",language="fr",format="PNG",lines=["Glycemie 68 mg/dL","HbA1c 5.4 %"],expectedNumbers=["68","5.4"],expectedUnits=["mg/dl","%"],expectedLabels=["Glycemie","HbA1c"],contrast=True),
    dict(id="fr_blur_jpeg",language="fr",format="JPEG",lines=["GLYCEMIE 132 mg/dL","HbA1c 7.4 %"],expectedNumbers=["132","7.4"],expectedUnits=["mg/dl","%"],expectedLabels=["GLYCEMIE","HbA1c"],blur=1.6),
    dict(id="fr_creatinine",language="fr",format="PNG",lines=["GLUCOSE 104 mg/dL","CREATININE 80 µmol/L"],expectedNumbers=["104","80"],expectedUnits=["mg/dl","µmol/l"],expectedLabels=["GLUCOSE","CREATININE"]),
    dict(id="ar_clean",language="ar",format="PNG",lines=["سكر الدم 54 mg/dL"],expectedNumbers=["54"],expectedUnits=["mg/dl"],expectedLabels=["سكر الدم"]),
    dict(id="ar_rotate",language="ar",format="PNG",lines=["السكر التراكمي 7.4 %"],expectedNumbers=["7.4"],expectedUnits=["%"],expectedLabels=["السكر التراكمي"],rotate=3.0),
    dict(id="mixed_clean",language="mixed",format="PNG",lines=["سكر الدم 126 mg/dL"],expectedNumbers=["126"],expectedUnits=["mg/dl"],expectedLabels=["سكر الدم"]),
)

def font_for(language):
    paths = (
        ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf","/usr/share/fonts/dejavu/DejaVuSans.ttf"]
        if language == "fr"
        else ["/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf","/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    )
    for path in paths:
        if Path(path).exists():
            return ImageFont.truetype(path,76)
    raise RuntimeError("Noto Arabic and DejaVu fonts required")

def generate(directory):
    directory.mkdir(parents=True,exist_ok=True)
    manifest=[]
    for case in CASES:
        contrast=case.get("contrast",False)
        image=Image.new("RGB",(1680,550),(225,225,225) if contrast else (255,255,255))
        draw=ImageDraw.Draw(image)
        font=font_for(case["language"])
        for i,line in enumerate(case["lines"]):
            ar=case["language"] != "fr"
            position=(1500,95+i*195) if ar else (75,95+i*195)
            if ar:
                draw.text(position,line,font=font,fill=(0,0,0),anchor="ra",direction="rtl",language="ar")
            else:
                draw.text(position,line,font=font,fill=(80,80,80) if contrast else (0,0,0))
        if case.get("rotate"):
            image=image.rotate(case["rotate"],resample=Image.Resampling.BICUBIC,fillcolor="white")
        if case.get("blur"):
            image=image.filter(ImageFilter.GaussianBlur(radius=case["blur"]))
        extension="jpg" if case["format"]=="JPEG" else "png"
        filename=f"{case['id']}.{extension}"
        image.save(directory/filename,format=case["format"],quality=55 if extension=="jpg" else None)
        manifest.append({key:value for key,value in case.items() if key in ("id","language","expectedNumbers","expectedUnits","expectedLabels")} | {"expectedLines":case["lines"],"filename":filename})
    (directory/"cases.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return len(manifest)

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    print(f"Generated {generate(args.output)} synthetic fixtures")
