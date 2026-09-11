#!/usr/bin/env python3
"""Cross-platform local launcher for IAMINA.

One canonical launcher for Windows and macOS.
Backend:  http://127.0.0.1:8008
Frontend: http://localhost:8009
"""

from __future__ import annotations

import argparse
import os
import platform
import re
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND_DIR = ROOT / "backend"
FRONTEND_DIR = ROOT / "frontend"
VENV_DIR = ROOT / "venv"
TOOL_VERSIONS = ROOT / ".tool-versions"
BACKEND_PORT = 8008
FRONTEND_PORT = 8009
REDIS_PORT = 6379
BACKEND_URL = f"http://127.0.0.1:{BACKEND_PORT}"
FRONTEND_URL = f"http://localhost:{FRONTEND_PORT}"
BACKEND_STARTUP_TIMEOUT = 300 if os.name == "nt" else 120


def log(message: str) -> None:
    print(message, flush=True)


def run(command: list[str], *, cwd: Path = ROOT, quiet: bool = False) -> None:
    kwargs: dict[str, object] = {"cwd": cwd, "check": True}
    if quiet:
        kwargs.update(stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(command, **kwargs)


def expected_tool_version(tool: str) -> str:
    if not TOOL_VERSIONS.exists():
        raise RuntimeError("Missing .tool-versions; cannot determine pinned toolchain versions.")
    for raw_line in TOOL_VERSIONS.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) >= 2 and parts[0] == tool:
            return parts[1]
    raise RuntimeError(f"Missing {tool} version in .tool-versions.")


def platform_name() -> str:
    if sys.platform == "win32":
        return "Windows"
    if sys.platform == "darwin":
        return "macOS"
    return platform.system() or sys.platform


def ensure_supported_platform() -> None:
    if sys.platform not in {"win32", "darwin"}:
        raise RuntimeError(
            f"IAMINA host launcher supports Windows and macOS; detected {platform_name()}."
        )


def install_hint(tool: str) -> str:
    expected_python = expected_tool_version("python")
    expected_flutter = expected_tool_version("flutter")
    if sys.platform == "win32":
        hints = {
            "python": (
                f"Install Python {expected_python}: "
                f"winget install -e --id Python.Python.{expected_python}"
            ),
            "flutter": (
                f"Install Flutter {expected_flutter} and add its bin directory to PATH: "
                "https://docs.flutter.dev/get-started/install/windows"
            ),
            "docker": (
                "Install/start Docker Desktop: "
                "winget install -e --id Docker.DockerDesktop"
            ),
            "git": "Install Git: winget install -e --id Git.Git",
        }
    else:
        hints = {
            "python": f"Install Python {expected_python}: brew install python@{expected_python}",
            "flutter": (
                f"Install Flutter {expected_flutter} and add it to PATH: "
                "https://docs.flutter.dev/get-started/install/macos"
            ),
            "docker": "Install/start Docker Desktop: brew install --cask docker",
            "git": "Install Git: xcode-select --install (or brew install git)",
        }
    return hints[tool]


def venv_python() -> Path:
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def port_is_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


def wait_for_tcp(host: str, port: int, process: subprocess.Popen[bytes], timeout: int) -> bool:
    """Wait until the local server is accepting TCP connections."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            return False
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            time.sleep(0.5)
    return False


def wait_for_http(url: str, process: subprocess.Popen[bytes], timeout: int = 120) -> bool:
    """Probe localhost directly, never through ambient HTTP(S) proxy settings."""
    deadline = time.monotonic() + timeout
    direct_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    while time.monotonic() < deadline:
        if process.poll() is not None:
            return False
        try:
            with direct_opener.open(url, timeout=1) as response:
                if response.status < 500:
                    return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def ensure_python_version() -> None:
    expected = expected_tool_version("python")
    current = f"{sys.version_info.major}.{sys.version_info.minor}"
    if current != expected:
        raise RuntimeError(
            f"IAMINA requires Python {expected}; current interpreter is "
            f"{sys.version.split()[0]}. {install_hint('python')}"
        )


def ensure_required_files() -> None:
    required = [
        BACKEND_DIR / "manage.py",
        BACKEND_DIR / "requirements.txt",
        FRONTEND_DIR / "pubspec.yaml",
        ROOT / ".env.example",
        TOOL_VERSIONS,
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
    if missing:
        raise RuntimeError("Missing required repository files: " + ", ".join(missing))


def flutter_command() -> str:
    flutter = shutil.which("flutter")
    if flutter:
        return flutter

    local_candidates = [
        ROOT / "flutter_sdk" / "flutter" / "bin" / "flutter.bat",
        ROOT / "flutter_sdk" / "flutter" / "bin" / "flutter",
    ]
    for candidate in local_candidates:
        if candidate.exists():
            return str(candidate)

    raise RuntimeError(
        f"Flutter {expected_tool_version('flutter')} was not found on PATH. "
        f"{install_hint('flutter')}"
    )


def docker_status() -> tuple[str, str | None]:
    docker = shutil.which("docker")
    if not docker:
        return "missing", None
    try:
        subprocess.run(
            [docker, "info"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10,
        )
        return "ready", docker
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return "stopped", docker


def environment_report(*, require_flutter: bool) -> int:
    ensure_supported_platform()
    ensure_required_files()

    failures: list[str] = []
    warnings: list[str] = []

    expected_python = expected_tool_version("python")
    current_python = f"{sys.version_info.major}.{sys.version_info.minor}"
    if current_python == expected_python:
        log(f"[PASS] Python {sys.version.split()[0]} (expected {expected_python})")
    else:
        failures.append(
            f"Python {expected_python} required; detected {sys.version.split()[0]}. "
            f"{install_hint('python')}"
        )

    git = shutil.which("git")
    if git:
        log(f"[PASS] Git found: {git}")
    else:
        warnings.append(f"Git not found. {install_hint('git')}")

    try:
        flutter = flutter_command()
        version = detected_flutter_version(flutter)
        expected_flutter = expected_tool_version("flutter")
        if version == expected_flutter:
            log(f"[PASS] Flutter {version} (expected {expected_flutter})")
        else:
            message = (
                f"Flutter {expected_flutter} required; detected {version}. "
                f"{install_hint('flutter')}"
            )
            if require_flutter:
                failures.append(message)
            else:
                warnings.append(message)
    except (RuntimeError, subprocess.CalledProcessError) as exc:
        if require_flutter:
            failures.append(str(exc))
        else:
            warnings.append(str(exc))

    docker_state, docker = docker_status()
    if docker_state == "ready":
        log(f"[PASS] Docker engine ready: {docker}")
    elif docker_state == "stopped":
        warnings.append(
            "Docker CLI is installed but the Docker engine is not running. "
            f"{install_hint('docker')}"
        )
    else:
        warnings.append(
            "Docker is not installed; Redis will use the backend fallback. "
            f"{install_hint('docker')}"
        )

    for port in (BACKEND_PORT, FRONTEND_PORT):
        if port_is_free(port):
            log(f"[PASS] Port {port} available")
        else:
            failures.append(f"Port {port} is already in use.")

    for message in warnings:
        log(f"[WARN] {message}")
    for message in failures:
        log(f"[FAIL] {message}")

    if failures:
        return 1
    log(f"CHECK PASS: platform={platform_name()} backend={BACKEND_PORT} frontend={FRONTEND_PORT}")
    return 0


def bootstrap() -> tuple[Path, str]:
    ensure_supported_platform()
    ensure_python_version()
    ensure_required_files()

    if not VENV_DIR.exists():
        log("==> Creating Python virtual environment")
        run([sys.executable, "-m", "venv", str(VENV_DIR)])

    python = venv_python()
    if not python.exists():
        raise RuntimeError(f"Virtual environment Python not found: {python}")

    log("==> Syncing backend dependencies")
    run([str(python), "-m", "pip", "install", "--quiet", "--upgrade", "pip"])
    run(
        [str(python), "-m", "pip", "install", "--quiet", "-r", str(BACKEND_DIR / "requirements.txt")]
    )

    env_path = ROOT / ".env"
    if not env_path.exists():
        shutil.copyfile(ROOT / ".env.example", env_path)
        log("==> Created .env from .env.example")

    log("==> Applying migrations")
    run([str(python), "manage.py", "migrate", "--run-syncdb", "-v", "0"], cwd=BACKEND_DIR)

    log("==> Ensuring demo data")
    try:
        run([str(python), "manage.py", "setup_demo"], cwd=BACKEND_DIR, quiet=True)
    except subprocess.CalledProcessError:
        log("[WARN] Demo setup did not complete; continuing with the existing database.")

    flutter = flutter_command()
    ensure_flutter_version(flutter)
    log("==> Syncing frontend dependencies")
    run([flutter, "pub", "get"], cwd=FRONTEND_DIR)
    return python, flutter


def redis_ping(docker: str, timeout: int = 20) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            result = subprocess.run(
                [docker, "exec", "iamina_redis", "redis-cli", "ping"],
                check=False,
                capture_output=True,
                text=True,
                timeout=3,
            )
            if result.returncode == 0 and result.stdout.strip() == "PONG":
                return True
        except subprocess.TimeoutExpired:
            pass
        time.sleep(0.5)
    return False


def start_redis() -> bool:
    docker_state, docker = docker_status()
    if docker_state == "missing":
        log(
            "[WARN] Docker not found; Redis will be unavailable. "
            + install_hint("docker")
        )
        return False
    if docker_state == "stopped" or docker is None:
        log(
            "[WARN] Docker is installed but its engine is not running; "
            "Redis will be unavailable. " + install_hint("docker")
        )
        return False

    try:
        existing = subprocess.run(
            [docker, "ps", "--filter", "name=^/iamina_redis$", "--format", "{{.Names}}"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        if existing == "iamina_redis":
            if redis_ping(docker):
                log("==> Redis already running and healthy (PONG)")
                return False
            log("[WARN] Existing iamina_redis container did not answer PING.")
            return False

        subprocess.run(
            [
                docker,
                "run",
                "-d",
                "--rm",
                "--name",
                "iamina_redis",
                "-p",
                f"{REDIS_PORT}:6379",
                "redis:7-alpine",
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if not redis_ping(docker):
            subprocess.run(
                [docker, "stop", "iamina_redis"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            log("[WARN] Redis container started but failed readiness PING; continuing without it.")
            return False

        log(f"==> Redis ready on localhost:{REDIS_PORT} (PONG)")
        return True
    except subprocess.CalledProcessError:
        log("[WARN] Redis could not be started; continuing without it.")
        return False


def stop_process(process: subprocess.Popen[bytes] | None) -> None:
    if process is None or process.poll() is not None:
        return
    try:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        else:
            os.killpg(process.pid, signal.SIGTERM)
        process.wait(timeout=8)
    except Exception:
        try:
            process.kill()
        except Exception:
            pass


def stop_redis_if_started(started: bool) -> None:
    if not started:
        return
    docker = shutil.which("docker")
    if docker:
        subprocess.run(
            [docker, "stop", "iamina_redis"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )


def popen(command: list[str], *, cwd: Path) -> subprocess.Popen[bytes]:
    kwargs: dict[str, object] = {"cwd": cwd}
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True
    return subprocess.Popen(command, **kwargs)


def launch(
    python: Path | str,
    flutter: str,
    *,
    open_browser: bool,
    smoke: bool,
    use_redis: bool,
) -> int:
    if not port_is_free(BACKEND_PORT):
        raise RuntimeError(f"Port {BACKEND_PORT} is already in use.")
    if not port_is_free(FRONTEND_PORT):
        raise RuntimeError(f"Port {FRONTEND_PORT} is already in use.")

    redis_started = start_redis() if use_redis else False
    backend: subprocess.Popen[bytes] | None = None
    frontend: subprocess.Popen[bytes] | None = None

    try:
        log(f"==> Starting backend  -> {BACKEND_URL}")
        backend = popen(
            [str(python), "manage.py", "runserver", f"127.0.0.1:{BACKEND_PORT}", "--noreload"],
            cwd=BACKEND_DIR,
        )
        if not wait_for_tcp("127.0.0.1", BACKEND_PORT, backend, timeout=BACKEND_STARTUP_TIMEOUT):
            raise RuntimeError(
                f"Backend failed to accept connections on port 8008 within {BACKEND_STARTUP_TIMEOUT}s."
            )

        log(f"==> Starting frontend -> {FRONTEND_URL}")
        frontend = popen(
            [
                flutter,
                "run",
                "-d",
                "web-server",
                "--web-port",
                str(FRONTEND_PORT),
                "--web-hostname",
                "localhost",
                "--dart-define=DEMO_EMAIL=dev@iamina.app",
                "--dart-define=DEMO_PASSWORD=IAmina2026!",
                "--dart-define=IAMINA_OFFLINE_DEMO=true",
                f"--dart-define=API_BASE_URL={BACKEND_URL}",
            ],
            cwd=FRONTEND_DIR,
        )
        if not wait_for_http(FRONTEND_URL, frontend):
            raise RuntimeError("Frontend failed to become ready on port 8009.")

        if smoke:
            log("SMOKE PASS: backend 8008 accepts connections and frontend 8009 is reachable.")
            return 0

        if open_browser:
            webbrowser.open(FRONTEND_URL)
        log("==> IAMINA is running. Press Ctrl-C to stop.")
        return frontend.wait()
    finally:
        stop_process(frontend)
        stop_process(backend)
        stop_redis_if_started(redis_started)


def detected_flutter_version(flutter: str) -> str:
    result = subprocess.run(
        [flutter, "--version"], capture_output=True, text=True, check=True
    )
    output = f"{result.stdout}\n{result.stderr}"
    match = re.search(r"\bFlutter\s+(\d+\.\d+\.\d+)\b", output)
    if not match:
        raise RuntimeError(
            "Could not detect Flutter version from `flutter --version` output."
        )
    return match.group(1)


def ensure_flutter_version(flutter: str) -> None:
    expected = expected_tool_version("flutter")
    version = detected_flutter_version(flutter)
    if version != expected:
        raise RuntimeError(
            f"Expected Flutter {expected}; detected {version}. {install_hint('flutter')}"
        )


def preflight(require_flutter: bool = True) -> int:
    result = environment_report(require_flutter=require_flutter)
    if result != 0:
        raise RuntimeError("Developer prerequisite check failed; see [FAIL] entries above.")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Launch IAMINA locally on Windows or macOS.")
    parser.add_argument("--check", action="store_true", help="Validate required launcher prerequisites.")
    parser.add_argument(
        "--doctor",
        action="store_true",
        help="Print developer-machine prerequisite diagnostics without launching IAMINA.",
    )
    parser.add_argument("--smoke", action="store_true", help="Start both services, probe them, then exit.")
    parser.add_argument(
        "--skip-bootstrap",
        action="store_true",
        help="Use the current Python environment and installed Flutter (CI/testing).",
    )
    parser.add_argument("--no-browser", action="store_true", help="Do not open the browser.")
    parser.add_argument("--no-redis", action="store_true", help="Do not attempt to start Redis via Docker.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.doctor:
            return environment_report(require_flutter=True)
        if args.check:
            return preflight()

        if args.skip_bootstrap:
            ensure_supported_platform()
            ensure_python_version()
            ensure_required_files()
            python: Path | str = sys.executable
            flutter = flutter_command()
            ensure_flutter_version(flutter)
        else:
            preflight()
            python, flutter = bootstrap()

        return launch(
            python,
            flutter,
            open_browser=not args.no_browser and not args.smoke,
            smoke=args.smoke,
            use_redis=not args.no_redis and not args.smoke,
        )
    except KeyboardInterrupt:
        log("\n==> Shutting down IAMINA")
        return 130
    except (RuntimeError, subprocess.CalledProcessError) as exc:
        log(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
