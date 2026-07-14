from __future__ import annotations

import io
import tempfile
import threading
import unittest
import urllib.request
from pathlib import Path
from unittest import mock

from scenariolens.local_server import (
    ExplorerServer,
    create_explorer_server,
    serve_explorer,
)


class LocalExplorerServerTest(unittest.TestCase):
    def test_server_exposes_explorer_and_run_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _write_explorer_fixture(root)
            server = create_explorer_server(root, port=0)
            thread = threading.Thread(target=server.httpd.serve_forever, daemon=True)
            thread.start()
            try:
                with urllib.request.urlopen(server.url, timeout=2) as response:
                    html = response.read().decode("utf-8")
                with urllib.request.urlopen(
                    server.url + "run.json",
                    timeout=2,
                ) as response:
                    run_payload = response.read().decode("utf-8")
            finally:
                server.httpd.shutdown()
                server.close()
                thread.join(timeout=2)

            self.assertIn("ScenarioLens test Explorer", html)
            self.assertIn("scenariolens.explorer_run.v1", run_payload)
            self.assertFalse(thread.is_alive())

    def test_server_rejects_incomplete_explorer(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaisesRegex(FileNotFoundError, "explorer/index.html"):
                create_explorer_server(tmpdir, port=0)

    def test_server_rejects_invalid_port(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _write_explorer_fixture(root)
            with self.assertRaisesRegex(ValueError, "between 0 and 65535"):
                create_explorer_server(root, port=70000)

    def test_server_reports_address_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _write_explorer_fixture(root)
            first = create_explorer_server(root, port=0)
            port = int(first.httpd.server_address[1])
            try:
                with self.assertRaisesRegex(RuntimeError, "Could not serve"):
                    create_explorer_server(root, port=port)
            finally:
                first.close()

    def test_serve_explorer_opens_browser_and_stops_cleanly(self) -> None:
        httpd = mock.Mock()
        httpd.serve_forever.side_effect = KeyboardInterrupt
        server = ExplorerServer(
            root=Path("/tmp/scenariolens-test"),
            url="http://127.0.0.1:8123/explorer/",
            httpd=httpd,
        )
        opened: list[str] = []
        output = io.StringIO()

        def open_browser(value: str) -> bool:
            opened.append(value)
            return True

        with mock.patch(
            "scenariolens.local_server.create_explorer_server",
            return_value=server,
        ):
            url = serve_explorer(
                run_dir=server.root,
                browser_opener=open_browser,
                output=output,
            )

        self.assertEqual(url, server.url)
        self.assertEqual(opened, [server.url])
        self.assertIn("Serving ScenarioLens Explorer", output.getvalue())
        self.assertIn("Stopping ScenarioLens Explorer", output.getvalue())
        httpd.server_close.assert_called_once_with()


def _write_explorer_fixture(root: Path) -> None:
    explorer = root / "explorer"
    explorer.mkdir(parents=True)
    (explorer / "index.html").write_text(
        "<!doctype html><title>ScenarioLens test Explorer</title>\n",
        encoding="utf-8",
    )
    (explorer / "app.js").write_text("\n", encoding="utf-8")
    (explorer / "styles.css").write_text("\n", encoding="utf-8")
    (explorer / "run.json").write_text(
        '{"format":"scenariolens.explorer_run.v1"}\n',
        encoding="utf-8",
    )
    (explorer / "scenarios.json").write_text(
        '{"format":"scenariolens.dashboard.v1"}\n',
        encoding="utf-8",
    )


if __name__ == "__main__":
    unittest.main()
