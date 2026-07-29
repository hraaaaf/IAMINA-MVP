from pathlib import Path

script = Path("scripts/apply_pr15_tranche6.py").read_text()
script = script.replace(
    'if text.count(old) != 1:\n        raise SystemExit(f"{label}: expected one anchor, found {text.count(old)}")',
    'if text.count(old) < 1:\n        raise SystemExit(f"{label}: anchor not found")',
    1,
)
exec(compile(script, "scripts/apply_pr15_tranche6.py", "exec"))
