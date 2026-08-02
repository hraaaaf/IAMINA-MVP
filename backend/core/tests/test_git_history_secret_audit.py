from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "audit_git_history_secrets.py"


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.name", "Synthetic Test")
    _git(repo, "config", "user.email", "synthetic@example.invalid")
    return repo


def _commit_all(repo: Path, message: str) -> None:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", message)


def _audit(repo: Path):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--repo", str(repo)],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def test_clean_history_passes(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "clean.txt").write_text("synthetic clean content\n")
    _commit_all(repo, "clean")

    result = _audit(repo)
    assert result.returncode == 0
    assert "passed" in result.stdout


def test_deleted_secret_still_fails_because_blob_is_reachable(tmp_path):
    repo = _init_repo(tmp_path)
    token = "sk-" + ("A" * 24)
    secret_path = repo / "config.txt"
    secret_path.write_text(f"API_KEY={token}\n")
    _commit_all(repo, "add synthetic credential")
    secret_path.unlink()
    _commit_all(repo, "remove file")

    result = _audit(repo)
    assert result.returncode == 1
    assert "generic sk token" in result.stderr
    assert token not in result.stderr


def test_historical_forbidden_env_path_fails_even_without_token(tmp_path):
    repo = _init_repo(tmp_path)
    env_path = repo / ".env"
    env_path.write_text("SYNTHETIC_CONFIGURATION=true\n")
    _commit_all(repo, "add forbidden path")
    env_path.unlink()
    _commit_all(repo, "remove forbidden path")

    result = _audit(repo)
    assert result.returncode == 1
    assert "forbidden credential/local-secret path" in result.stderr
    assert "SYNTHETIC_CONFIGURATION" not in result.stderr


def test_firebase_client_google_identifier_exception_is_path_scoped(tmp_path):
    repo = _init_repo(tmp_path)
    identifier = "AIza" + ("A" * 35)
    allowed = repo / "frontend" / "lib"
    allowed.mkdir(parents=True)
    (allowed / "firebase_options.dart").write_text(f"apiKey: '{identifier}'\n")
    _commit_all(repo, "add synthetic firebase client config")

    assert _audit(repo).returncode == 0

    other = repo / "backend.txt"
    other.write_text(f"api_key={identifier}\n")
    _commit_all(repo, "reuse identifier outside allowed path")
    result = _audit(repo)
    assert result.returncode == 1
    assert "Google API key" in result.stderr
    assert identifier not in result.stderr
