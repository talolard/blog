"""pytest fixtures for Playwright UI tests.

We run Playwright against a real `hugo server` process so tests verify the
rendered HTML and asset pipeline (Hugo + SCSS) as a user would see it.
"""

from __future__ import annotations

import os
import socket
import subprocess
import time
from collections.abc import Iterator
from pathlib import Path

import pytest


def _find_free_port() -> int:
    """Allocate an ephemeral TCP port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _repo_root() -> Path:
    """Return the repository root from this file's location."""
    return Path(__file__).resolve().parents[3]


def _wait_for_http(url: str, *, timeout_s: float) -> None:
    """Wait until `url` starts responding (or timeout)."""
    import urllib.request

    deadline = time.monotonic() + timeout_s
    last_error: Exception | None = None

    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if 200 <= response.status < 500:
                    return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
        time.sleep(0.05)

    raise RuntimeError(f"Timed out waiting for {url}") from last_error


@pytest.fixture(scope="session")
def hugo_server_base_url() -> Iterator[str]:
    """Start `hugo server` once per session and yield its base URL."""
    repo_root = _repo_root()
    port = _find_free_port()
    base_url = f"http://127.0.0.1:{port}"

    env = os.environ.copy()
    env["HUGO_ENVIRONMENT"] = "development"

    process = subprocess.Popen(
        [
            "hugo",
            "server",
            "--bind",
            "127.0.0.1",
            "--port",
            str(port),
            "--disableFastRender",
            "--gc",
        ],
        cwd=repo_root,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        _wait_for_http(f"{base_url}/en/", timeout_s=15)
        yield base_url
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)


@pytest.fixture(scope="session")
def base_url(hugo_server_base_url: str) -> str:
    """Compatibility fixture for pytest-playwright's `base_url` integration."""
    return hugo_server_base_url
