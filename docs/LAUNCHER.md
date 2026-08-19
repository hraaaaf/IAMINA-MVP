# IAMINA local launcher

`IAMINA.py` is the single source of launcher logic and remains the canonical CLI entry point.

Guaranteed CLI paths:

- Windows: `python IAMINA.py`
- macOS: `python3 IAMINA.py`

Native double-click entry points are deliberately thin wrappers over that same file:

- Windows: double-click `IAMINA.bat`
- macOS: double-click `IAMINA.command`

The wrappers do not duplicate bootstrap, dependency, port, readiness or process-management logic. They only move to the repository root, invoke `IAMINA.py`, forward arguments and preserve its exit code. `IAMINA.command` is versioned executable so Finder can open it through Terminal after a normal Git checkout.

Required developer toolchains remain unchanged: Git, Python 3.12, Flutter 3.41.7 and a Chromium/Chrome-class browser.

Runtime endpoints:

- backend: `http://127.0.0.1:8008`
- frontend: `http://localhost:8009`

The portability workflow certifies the real path on both operating systems: native wrapper → `IAMINA.py` → full bootstrap → backend/frontend reachability → cleanup.

See `docs/DEPENDENCIES.md` for prerequisites and `docs/assessments/2026-08-19-single-cross-platform-launcher-audit.md` for the underlying launcher audit and certification contract.
