"""Synthetic, non-patient benchmark through the exact IAMINA demo model path."""
import argparse
import json
import os
import sys
from pathlib import Path

# Running a file inside backend/evaluation puts only that subdirectory on sys.path.
# Add backend explicitly so Django settings and production modules resolve exactly as in manage.py.
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "amina.settings")
os.environ["IAMINA_DEMO_EXTERNAL_AI_ENABLED"] = "true"
os.environ["IAMINA_DEMO_LLM_PROVIDER"] = "groq"

import django  # noqa: E402

django.setup()

from companion.demo_model import generate_demo_reply  # noqa: E402

MODELS = ["openai/gpt-oss-120b","allam-2-7b"]
PROMPTS = [
("darija-latin","fr","fia doukha"),("darija-latin","fr","ma fhemtch chno glti"),
("darija-latin","fr","3ndi sda3 mn sba7"),("darija-latin","fr","wach t9der tchra7 lia hadchi b darija?"),
("darija-latin","fr","kan7ess brassi 3yan bezaf lyouma"),("darija-ar","ar-MA","شنو نقدر ندير باش نفهم هاد النتيجة؟"),
("darija-ar","ar-MA","واش تقدر تشرح ليا بالدارجة؟"),
("english","en","I feel dizzy today."),("english","en","Can you explain this in simple English?"),
("english","en","What languages can you speak?"),
("gulf","ar","ممكن تشرح لي بطريقة أبسط؟"),("gulf","ar","أنا تعبان شوي اليوم وش أسوي؟"),
("gulf","ar","تقدر تكلمني باللهجة الخليجية؟")]
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    if not os.environ.get("GROQ_API_KEY"):
        raise SystemExit("GROQ_API_KEY missing")

    rows = []
    for model in MODELS:
        os.environ["IAMINA_DEMO_LLM_MODEL"] = model
        for locale, language, prompt in PROMPTS:
            try:
                reply = generate_demo_reply(prompt, language)
                rows.append(
                    {
                        "model": model,
                        "locale": locale,
                        "prompt": prompt,
                        "reply": reply,
                        "error": None,
                    }
                )
            except Exception as exc:
                rows.append(
                    {
                        "model": model,
                        "locale": locale,
                        "prompt": prompt,
                        "reply": "",
                        "error": type(exc).__name__ + ": " + str(exc)[:300],
                    }
                )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            {
                "synthetic": True,
                "production_path": True,
                "models": MODELS,
                "rows": rows,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
