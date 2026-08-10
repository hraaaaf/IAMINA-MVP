from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "check_ai_egress_boundaries.py"


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


def _write(repo: Path, relative: str, content: str) -> None:
    path = repo / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _commit(repo: Path) -> None:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "synthetic gate fixture")


def _run(repo: Path, check: str):
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--repo",
            str(repo),
            "--check",
            check,
        ],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def test_gateway_gate_allows_only_sanctioned_paths(tmp_path):
    repo = _init_repo(tmp_path)
    _write(
        repo,
        "backend/core/llm_gateway.py",
        "def get_llm():\n    assert_ai_egress_allowed()\n",
    )
    _write(repo, "backend/core/tests/test_gateway.py", "get_llm()\n")
    _commit(repo)

    result = _run(repo, "gateway")
    assert result.returncode == 0
    assert "passed" in result.stdout


def test_gateway_gate_rejects_unauthorized_tracked_callsite(tmp_path):
    repo = _init_repo(tmp_path)
    _write(repo, "backend/rogue.py", "client = get_llm()\n")
    _commit(repo)

    result = _run(repo, "gateway")
    assert result.returncode == 1
    assert "LLM gateway anti-bypass: FAILED" in result.stderr
    assert "rogue.py" in result.stderr
    assert "client =" not in result.stderr


def test_egress_gate_rejects_callsite_without_central_authorization(tmp_path):
    repo = _init_repo(tmp_path)
    _write(repo, "backend/ai/api/v1/ai.py", "client = genai.Client()\n")
    _commit(repo)

    result = _run(repo, "egress")
    assert result.returncode == 1
    assert "AI egress authorization anti-bypass: FAILED" in result.stderr
    assert "ai/api/v1/ai.py" in result.stderr
    assert "client =" not in result.stderr


def test_egress_gate_accepts_callsite_with_direct_central_assertion(tmp_path):
    repo = _init_repo(tmp_path)
    _write(
        repo,
        "backend/ai/api/v1/ai.py",
        "assert_ai_egress_allowed()\nclient = genai.Client()\n",
    )
    _commit(repo)

    result = _run(repo, "egress")
    assert result.returncode == 0


def test_egress_gate_accepts_callsite_using_central_runtime_wrapper(tmp_path):
    repo = _init_repo(tmp_path)
    _write(
        repo,
        "backend/media/vision.py",
        "client = genai.Client()\n"
        "execute_external_provider_call('gemini', 'image', 'vision', lambda: client.run())\n",
    )
    _commit(repo)

    result = _run(repo, "egress")
    assert result.returncode == 0


def test_import_or_comment_cannot_impersonate_runtime_authorization(tmp_path):
    repo = _init_repo(tmp_path)
    _write(
        repo,
        "backend/media/vision.py",
        "from llm.runtime import execute_external_provider_call\n"
        "# assert_ai_egress_allowed() and execute_external_provider_call() would be safe\n"
        "client = genai.Client()\n",
    )
    _commit(repo)

    result = _run(repo, "egress")
    assert result.returncode == 1
    assert "media/vision.py" in result.stderr


def test_egress_gate_detects_whitespace_before_call_parenthesis(tmp_path):
    repo = _init_repo(tmp_path)
    _write(repo, "backend/ai/api/v1/ai.py", "client = GenerativeModel   ('x')\n")
    _commit(repo)

    result = _run(repo, "egress")
    assert result.returncode == 1
    assert "ai/api/v1/ai.py" in result.stderr


def test_tests_migrations_and_provider_adapter_are_excluded_from_egress_gate(tmp_path):
    repo = _init_repo(tmp_path)
    _write(repo, "backend/core/tests/test_ai.py", "genai.Client()\n")
    _write(repo, "backend/foo/migrations/0001_initial.py", "GenerativeModel()\n")
    _write(repo, "backend/llm/provider.py", "get_llm()\n")
    _commit(repo)

    result = _run(repo, "egress")
    assert result.returncode == 0


def test_untracked_local_file_cannot_change_gate_result(tmp_path):
    repo = _init_repo(tmp_path)
    _write(
        repo,
        "backend/ai/api/v1/ai.py",
        "assert_ai_egress_allowed()\nclient = genai.Client()\n",
    )
    _commit(repo)
    _write(repo, "backend/untracked_rogue.py", "get_llm()\n")

    assert _run(repo, "gateway").returncode == 0
    assert _run(repo, "egress").returncode == 0


def test_tracked_python_syntax_error_fails_egress_gate_closed(tmp_path):
    repo = _init_repo(tmp_path)
    _write(repo, "backend/broken.py", "def broken(:\n")
    _commit(repo)

    result = _run(repo, "egress")
    assert result.returncode == 2
    assert "AI boundary gate ERROR" in result.stderr
    assert "broken.py" in result.stderr


def test_gate_fails_closed_when_repo_cannot_be_enumerated(tmp_path):
    not_a_repo = tmp_path / "not-a-repo"
    not_a_repo.mkdir()

    result = _run(not_a_repo, "gateway")
    assert result.returncode == 2
    assert "AI boundary gate ERROR" in result.stderr
