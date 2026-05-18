#!/usr/bin/env python3
"""Local development server for the sandbox version.

The frontend is mostly static, but it needs a tiny API to persist settings to
`data/user_settings.json`. This keeps the project framework-free while still
letting the UI update the Python scripts' input data.
"""
from __future__ import annotations

import json
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
    server = ThreadingHTTPServer(("127.0.0.1", 8001), AwakeningHandler)
    print("Serving Awakening System on http://127.0.0.1:8001/")
    server.serve_forever()


if __name__ == "__main__":
    main()
