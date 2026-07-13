from __future__ import annotations

import sys
import webbrowser
from dataclasses import dataclass
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable, TextIO

DEFAULT_EXPLORER_HOST = "127.0.0.1"
DEFAULT_EXPLORER_PORT = 8000

_REQUIRED_EXPLORER_FILES = (
    "explorer/index.html",
    "explorer/app.js",
    "explorer/styles.css",
    "explorer/run.json",
    "explorer/scenarios.json",
)


@dataclass(frozen=True)
class ExplorerServer:
    """A configured local HTTP server for one ScenarioLens run bundle."""

    root: Path
    url: str
    httpd: ThreadingHTTPServer

    def close(self) -> None:
        self.httpd.server_close()


class _ExplorerRequestHandler(SimpleHTTPRequestHandler):
    def log_message(self, format_string: str, *args: object) -> None:
        return


def create_explorer_server(
    run_dir: str | Path,
    host: str = DEFAULT_EXPLORER_HOST,
    port: int = DEFAULT_EXPLORER_PORT,
) -> ExplorerServer:
    """Create a local server after validating the generated Explorer bundle."""

    root = Path(run_dir).resolve()
    missing = [
        relative
        for relative in _REQUIRED_EXPLORER_FILES
        if not (root / relative).is_file()
    ]
    if missing:
        joined = ", ".join(missing)
        raise FileNotFoundError(
            f"ScenarioLens Explorer is incomplete under {root}; missing: {joined}"
        )
    if not 0 <= port <= 65535:
        raise ValueError("Explorer port must be between 0 and 65535.")

    handler = partial(_ExplorerRequestHandler, directory=str(root))
    try:
        httpd = ThreadingHTTPServer((host, port), handler)
    except OSError as exc:
        raise RuntimeError(
            f"Could not serve ScenarioLens Explorer on {host}:{port}: {exc}"
        ) from exc
    httpd.daemon_threads = True
    actual_port = int(httpd.server_address[1])
    browser_host = _browser_host(host)
    return ExplorerServer(
        root=root,
        url=f"http://{browser_host}:{actual_port}/explorer/",
        httpd=httpd,
    )


def serve_explorer(
    run_dir: str | Path,
    host: str = DEFAULT_EXPLORER_HOST,
    port: int = DEFAULT_EXPLORER_PORT,
    launch_browser: bool = True,
    browser_opener: Callable[[str], bool] | None = None,
    output: TextIO | None = None,
) -> str:
    """Serve a run bundle until interrupted and return the local Explorer URL."""

    stream = output or sys.stdout
    server = create_explorer_server(run_dir=run_dir, host=host, port=port)
    print(f"Serving ScenarioLens Explorer at {server.url}", file=stream, flush=True)
    print("Press Ctrl+C to stop the local server.", file=stream, flush=True)

    if launch_browser:
        opener = browser_opener or webbrowser.open
        try:
            opened = opener(server.url)
        except (OSError, webbrowser.Error) as exc:
            opened = False
            print(
                f"Could not open a browser automatically: {exc}",
                file=stream,
                flush=True,
            )
        if not opened:
            print(
                "Open the URL above in a browser to inspect the run.",
                file=stream,
                flush=True,
            )

    try:
        server.httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping ScenarioLens Explorer.", file=stream, flush=True)
    finally:
        server.close()
    return server.url


def _browser_host(host: str) -> str:
    if host in {"", "0.0.0.0", "::"}:
        return "127.0.0.1"
    if ":" in host and not host.startswith("["):
        return f"[{host}]"
    return host
