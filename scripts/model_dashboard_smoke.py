#!/usr/bin/env python3
"""One-command smoke checks for the Local Model Performance Dashboard."""

import argparse
import shlex
import socket
import subprocess
import sys
import tempfile
import time
from ipaddress import ip_address
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

REPO_ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_CLI = REPO_ROOT / "apps" / "model-dashboard" / "run_dashboard.py"
TEST_DIR = REPO_ROOT / "apps" / "model-dashboard" / "tests"
SERVER_PATHS = (
    "/",
    "/?label=CODING_SPECIALIST&keep=yes",
    "/lab",
    "/runs",
    "/runs?backend=llama.cpp",
    "/reviews",
    "/compare?status=confirmed",
    "/inventory",
    "/inventory?runtime=LM%20Studio",
    "/radar",
    "/radar?security=needs_review",
    "/specialty",
    "/specialty?lane=Dolphin",
    "/specialty?security=needs_review",
    "/projects",
    "/storage",
    "/storage?keep=yes",
    "/reports",
    "/demo",
    "/models/3",
)
SERVER_CONTENT = {
    "/": "Local Readiness",
    "/lab": "Local Readiness",
    "/reviews": "Draft Review Queue",
}


class SmokeFailure(RuntimeError):
    pass


def _shell_join(command):
    return " ".join(shlex.quote(str(part)) for part in command)


def _run_step(label, command, timeout):
    print(f"\n==> {label}", flush=True)
    print(f"$ {_shell_join(command)}", flush=True)
    try:
        proc = subprocess.run(
            [str(part) for part in command],
            cwd=str(REPO_ROOT),
            text=True,
            capture_output=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise SmokeFailure(f"{label} timed out after {timeout} seconds") from exc
    if proc.stdout:
        print(proc.stdout.rstrip())
    if proc.stderr:
        print(proc.stderr.rstrip(), file=sys.stderr)
    if proc.returncode != 0:
        raise SmokeFailure(f"{label} failed with exit code {proc.returncode}")


def _free_local_port(host):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        return sock.getsockname()[1]


def _request(url, timeout):
    with urlopen(url, timeout=timeout) as response:
        body = response.read().decode("utf-8", errors="replace")
        return response.status, body


def _loopback_host(value):
    host = str(value).strip()
    if host == "localhost":
        return host
    try:
        address = ip_address(host)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "--host must be localhost or an IPv4 loopback address."
        ) from exc
    if address.version == 4 and address.is_loopback:
        return host
    raise argparse.ArgumentTypeError("--host must be localhost or an IPv4 loopback address.")


def _probe_server(db_path, host, timeout):
    try:
        port = _free_local_port(host)
    except OSError as exc:
        raise SmokeFailure(f"Could not reserve a local probe port on {host}: {exc}") from exc
    command = [
        sys.executable,
        DASHBOARD_CLI,
        "serve",
        "--db",
        db_path,
        "--host",
        host,
        "--port",
        port,
    ]
    print("\n==> Probe local server", flush=True)
    print(f"$ {_shell_join(command)}", flush=True)

    proc = subprocess.Popen(
        [str(part) for part in command],
        cwd=str(REPO_ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    output = ""
    try:
        root_url = f"http://{host}:{port}{SERVER_PATHS[0]}"
        deadline = time.monotonic() + timeout
        last_error = None
        while time.monotonic() < deadline:
            if proc.poll() is not None:
                output = proc.stdout.read() if proc.stdout else ""
                raise SmokeFailure(
                    f"Dashboard server exited before probe completed.\n{output.rstrip()}"
                )
            try:
                status, body = _request(root_url, timeout=1)
                if status == 200 and "Local Model Performance Dashboard" in body:
                    break
            except URLError as exc:
                last_error = exc
                time.sleep(0.1)
        else:
            raise SmokeFailure(f"Timed out waiting for {root_url}: {last_error}")

        for path in SERVER_PATHS:
            url = f"http://{host}:{port}{path}"
            try:
                status, body = _request(url, timeout=timeout)
            except (OSError, URLError) as exc:
                raise SmokeFailure(f"{url} request failed: {exc}") from exc
            if status != 200:
                raise SmokeFailure(f"{url} returned HTTP {status}")
            if "Local Model Performance Dashboard" not in body:
                raise SmokeFailure(f"{url} did not render the dashboard shell")
            expected = SERVER_CONTENT.get(path)
            if expected and expected not in body:
                raise SmokeFailure(f"{url} did not render expected content: {expected}")
            print(f"OK {path} -> HTTP {status}", flush=True)
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                output = proc.communicate(timeout=5)[0] or output
            except subprocess.TimeoutExpired:
                proc.kill()
                output = proc.communicate(timeout=5)[0] or output
        if output.strip():
            print(output.rstrip())


def build_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Run dashboard tests, fixture DB init, report generation, and optional server probe."
        )
    )
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        help="Directory for smoke artifacts. Defaults to a new system temp directory.",
    )
    parser.add_argument(
        "--probe-server",
        action="store_true",
        help="Start the local dashboard server and probe key pages.",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        type=_loopback_host,
        help="Loopback host for --probe-server. Defaults to 127.0.0.1.",
    )
    parser.add_argument("--timeout", type=float, default=20.0)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    artifact_dir = args.artifact_dir or Path(tempfile.mkdtemp(prefix="model-dashboard-smoke-"))
    artifact_dir = artifact_dir.resolve()
    artifact_dir.mkdir(parents=True, exist_ok=True)

    db_path = artifact_dir / "model_dashboard.sqlite"
    report_path = artifact_dir / "fixture-model-report.md"

    print(f"Smoke artifacts: {artifact_dir}", flush=True)
    _run_step(
        "Run dashboard tests",
        [sys.executable, "-m", "unittest", "discover", "-s", TEST_DIR],
        args.timeout,
    )
    _run_step(
        "Initialize fixture database",
        [
            sys.executable,
            DASHBOARD_CLI,
            "init-db",
            "--db",
            db_path,
            "--reset",
            "--with-fixtures",
        ],
        args.timeout,
    )
    _run_step(
        "Generate fixture report",
        [
            sys.executable,
            DASHBOARD_CLI,
            "report",
            "--db",
            db_path,
            "--out",
            report_path,
        ],
        args.timeout,
    )

    if not report_path.exists():
        raise SmokeFailure(f"Expected report was not written: {report_path}")
    if args.probe_server:
        _probe_server(db_path, args.host, args.timeout)

    print("\nDashboard smoke passed.", flush=True)
    print(f"Database: {db_path}", flush=True)
    print(f"Report: {report_path}", flush=True)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SmokeFailure as exc:
        print(f"\nDashboard smoke failed: {exc}", file=sys.stderr)
        sys.exit(1)
