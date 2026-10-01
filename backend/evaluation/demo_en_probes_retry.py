"""Minimal Groq retry: 1 EN open turn + 3-turn memory check."""

from __future__ import annotations

import importlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _reply(message: str, history: list[dict[str, str]] | None = None) -> dict:
    demo = importlib.import_module("companion.demo")
    return demo.reply_to_demo_message(message, language="en", history=history or [])


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "amina.settings")
    os.environ["IAMINA_DEMO_EXTERNAL_AI_ENABLED"] = "true"
    os.environ["IAMINA_DEMO_LLM_PROVIDER"] = "groq"
    os.environ["IAMINA_DEMO_LLM_MODEL"] = "openai/gpt-oss-120b"

    django = importlib.import_module("django")
    django.setup()

    out = {"model": "openai/gpt-oss-120b", "max_expected_groq_calls": 4, "open": None, "multiturn": []}

    try:
        payload = _reply("I had a rough day. Just talk to me normally, no diagnosis.")
        out["open"] = {
            "reply": payload["reply"],
            "reply_language": payload["reply_language"],
            "is_emergency": payload["is_emergency"],
            "error": None,
        }
    except Exception as exc:
        out["open"] = {"reply": "", "error": f"{type(exc).__name__}: {str(exc)[:400]}"}

    history: list[dict[str, str]] = []
    prompts = [
        "Remember only this word: Atlas.",
        "Add Cedar. What are the two words in order?",
        "What was the first word only?",
    ]
    for index, prompt in enumerate(prompts, 1):
        try:
            payload = _reply(prompt, history)
            reply = payload["reply"]
            out["multiturn"].append(
                {
                    "turn": index,
                    "prompt": prompt,
                    "reply": reply,
                    "reply_language": payload["reply_language"],
                    "error": None,
                }
            )
            history.extend(
                [
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": reply},
                ]
            )
        except Exception as exc:
            out["multiturn"].append(
                {
                    "turn": index,
                    "prompt": prompt,
                    "reply": "",
                    "error": f"{type(exc).__name__}: {str(exc)[:400]}",
                }
            )
            break

    target = Path("../artifacts/demo-en-probes-retry.json")
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
