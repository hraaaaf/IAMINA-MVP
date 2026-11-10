"""Fail closed if production Flutter HTTP transport enables raw request logging.

This checks a narrow, observable invariant, not all possible data leakage.
"""
from pathlib import Path
import re
import sys

FORBIDDEN = re.compile(
    r"\b(?:CurlInterceptor|HttpLoggingInterceptor|LoggingInterceptor)\s*\("
)

def violations(frontend_lib: Path) -> list[str]:
    client = frontend_lib / "services" / "api_client.dart"
    if not client.is_file():
        return [f"missing transport client: {client}"]
    source = client.read_text(encoding="utf-8")
    if not re.search(r"\bAuthInterceptor\s*\(", source):
        return ["missing AuthInterceptor in transport client; review transport chain"]
    failures = []
    for path in sorted(frontend_lib.rglob("*.dart")):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            # Ignore explanatory comments, but not executable expressions.
            code = line.split("//", 1)[0]
            if FORBIDDEN.search(code):
                failures.append(f"{path}:{number}: raw HTTP logging interceptor")
    return failures

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    errors = violations(root / "frontend" / "lib")
    if errors:
        for error in errors:
            print(f"PRIVACY LOG GATE FAIL: {error}", file=sys.stderr)
        sys.exit(1)
    print("PRIVACY LOG GATE PASS: no raw HTTP logging interceptors in frontend/lib")
