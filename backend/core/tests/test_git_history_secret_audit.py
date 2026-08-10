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


def test_current_firebase_client_identifier_is_allowed_in_compiled_artifact(tmp_path):
    repo = _init_repo(tmp_path)
    identifier = "AIza" + ("A" * 35)
    allowed = repo / "frontend" / "lib"
    allowed.mkdir(parents=True)
    (allowed / "firebase_options.dart").write_text(f"apiKey: '{identifier}'\n")
    _commit_all(repo, "add synthetic firebase client config")

    compiled = repo / "main.dart.js"
    compiled.write_text(f"compiledFirebaseConfig='{identifier}'\n")
    _commit_all(repo, "add compiled client config")

    assert _audit(repo).returncode == 0


def test_known_firebase_identifier_outside_compiled_artifact_still_fails(tmp_path):
    repo = _init_repo(tmp_path)
    identifier = "AIza" + ("A" * 35)
    allowed = repo / "frontend" / "lib"
    allowed.mkdir(parents=True)
    (allowed / "firebase_options.dart").write_text(f"apiKey: '{identifier}'\n")
    (repo / "backend.txt").write_text(f"api_key={identifier}\n")
    _commit_all(repo, "reuse known client identifier outside compiled artifact")

    result = _audit(repo)
    assert result.returncode == 1
    assert "Google API key" in result.stderr
    assert identifier not in result.stderr


def test_unknown_google_identifier_in_compiled_artifact_still_fails(tmp_path):
    repo = _init_repo(tmp_path)
    known_identifier = "AIza" + ("A" * 35)
    unknown_identifier = "AIza" + ("B" * 35)
    allowed = repo / "frontend" / "lib"
    allowed.mkdir(parents=True)
    (allowed / "firebase_options.dart").write_text(f"apiKey: '{known_identifier}'\n")
    (repo / "main.dart.js").write_text(f"otherKey='{unknown_identifier}'\n")
    _commit_all(repo, "add known and unknown Google-format identifiers")

    result = _audit(repo)
    assert result.returncode == 1
    assert "Google API key" in result.stderr
    assert unknown_identifier not in result.stderr


def test_known_synthetic_sk_fixture_is_ignored_in_reachable_history(tmp_path):
    repo = _init_repo(tmp_path)
    fixture = "sk-" + "this-must-never-be-in-the-manifest"
    fixture_path = repo / "test_fixture.py"
    fixture_path.write_text(f"api_key = '{fixture}'\n")
    _commit_all(repo, "add known synthetic fixture")
    fixture_path.unlink()
    _commit_all(repo, "remove known synthetic fixture")

    assert _audit(repo).returncode == 0


def test_known_synthetic_sk_fixture_exception_is_exact(tmp_path):
    repo = _init_repo(tmp_path)
    fixture_like_value = "sk-" + "this-must-never-be-in-the-manifest-extra"
    path = repo / "fixture_like.txt"
    path.write_text(f"api_key = '{fixture_like_value}'\n")
    _commit_all(repo, "add fixture-like token")

    result = _audit(repo)
    assert result.returncode == 1
    assert "generic sk token" in result.stderr
    assert fixture_like_value not in result.stderr


def test_safe_sk_example_cannot_hide_another_credential_on_same_line(tmp_path):
    repo = _init_repo(tmp_path)
    safe_example = "sk-" + "example-" + ("A" * 20)
    aws_identifier = "AKIA" + ("B" * 16)
    path = repo / "mixed.txt"
    path.write_text(f"EXAMPLE={safe_example} AWS={aws_identifier}\n")
    _commit_all(repo, "add mixed synthetic line")

    result = _audit(repo)
    assert result.returncode == 1
    assert "AWS access key" in result.stderr
    assert aws_identifier not in result.stderr


def test_shallow_repository_is_rejected(tmp_path):
    source = _init_repo(tmp_path)
    (source / "clean.txt").write_text("clean\n")
    _commit_all(source, "clean")

    clone = tmp_path / "shallow"
    subprocess.run(
        ["git", "clone", "--depth", "1", source.as_uri(), str(clone)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    result = _audit(clone)
    assert result.returncode == 2
    assert "non-shallow checkout" in result.stderr
