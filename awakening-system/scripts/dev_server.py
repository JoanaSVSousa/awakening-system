#!/usr/bin/env python3
"""Local development server for the sandbox version.

The frontend is mostly static, but it needs a tiny API to persist settings to
`data/user_settings.json`. This keeps the project framework-free while still
letting the UI update the Python scripts' input data.
"""
from __future__ import annotations

import json
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
SETTINGS_PATH = ROOT / "data" / "user_settings.json"


class AwakeningHandler(SimpleHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def send_json(self, data: dict, status: int = 200) -> None:
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        request_path = urlparse(self.path).path
        if request_path == "/healthz":
            self.send_json({"ok": True})
            return

        if request_path == "/":
            self.send_response(302)
            self.send_header("Location", "/web/index.html")
            self.end_headers()
            return

        if request_path == "/api/settings":
            if not SETTINGS_PATH.exists():
                self.send_json({})
                return

            with SETTINGS_PATH.open("r", encoding="utf-8") as file:
                self.send_json(json.load(file))
            return

        super().do_GET()

    def do_POST(self) -> None:
        if self.path != "/api/settings":
            self.send_error(404)
            return

        length = int(self.headers.get("Content-Length", "0"))
        payload = self.rfile.read(length)
        try:
            settings = json.loads(payload.decode("utf-8"))
        except json.JSONDecodeError:
            self.send_json({"error": "Invalid JSON payload."}, status=400)
            return

        SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with SETTINGS_PATH.open("w", encoding="utf-8") as file:
            json.dump(settings, file, indent=2)
            file.write("\n")

        self.send_json({"ok": True, "settings": settings})


def main() -> None:
    # Render provides PORT at runtime and requires services to bind to 0.0.0.0.
    # Local development still defaults to http://127.0.0.1:8001/.
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8001"))
    if os.environ.get("RENDER"):
        host = "0.0.0.0"

    server = ThreadingHTTPServer((host, port), AwakeningHandler)
    print(f"Serving Awakening System on http://{host}:{port}/")
    server.serve_forever()


if __name__ == "__main__":
    main()
