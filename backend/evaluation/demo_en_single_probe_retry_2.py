"""Single English Groq availability probe with exception-chain evidence."""

from __future__ import annotations

import importlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _exc_chain(exc: BaseException) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    seen: set[int] = set()
    cur: BaseException | None = exc
    while cur is not None and id(cur) not in seen and len(out) < 6:
        seen.add(id(cur))
        out.append({"type": type(cur).__name__, "message": str(cur)[:1000], "repr": repr(cur)[:1200]})
        cur = cur.__cause__ or cur.__context__
    return out


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "amina.settings")
    os.environ["IAMINA_DEMO_EXTERNAL_AI_ENABLED"] = "true"
    os.environ["IAMINA_DEMO_LLM_PROVIDER"] = "groq"
    os.environ["IAMINA_DEMO_LLM_MODEL"] = "openai/gpt-oss-120b"

    django = importlib.import_module("django")
    django.setup()
    demo = importlib.import_module("companion.demo")

    result: dict = {
        "model": "openai/gpt-oss-120b",
        "max_expected_groq_calls": 1,
        "prompt": "I had a rough day. Just talk to me normally, no diagnosis.",
    }
    try:
        payload = demo.reply_to_demo_message(result["prompt"], language="en", history=[])
        result.update(
            {
                "reply": payload["reply"],
                "reply_language": payload["reply_language"],
                "is_emergency": payload["is_emergency"],
                "error": None,
            }
        )
    except Exception as exc:
        result.update({"reply": "", "error": _exc_chain(exc)})

    target = Path("../artifacts/demo-en-single-probe-retry-2.json")
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
