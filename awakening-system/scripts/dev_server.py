#!/usr/bin/env python3
"""Local development server for the sandbox version.

The frontend is mostly static, but it needs a tiny API to persist settings to
`data/user_settings.json`. This keeps the project framework-free while still
letting the UI update the Python scripts' input data.
"""
from __future__ import annotations

import hmac
import json
import os
import secrets
from http import cookies
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
SETTINGS_PATH = ROOT / "data" / "user_settings.json"
QUESTS_PATH = ROOT / "data" / "quests.json"
ENV_PATH = ROOT / ".env"
SESSION_COOKIE = "awakening_session"
SESSIONS: set[str] = set()


def load_env_file(path: Path = ENV_PATH) -> None:
    """Load local private configuration without requiring python-dotenv."""
    if not path.exists():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue

        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def env_flag(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def auth_enabled() -> bool:
    return env_flag("AUTH_ENABLED", default=False)


class AwakeningHandler(SimpleHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def send_json(self, data: dict | list, status: int = 200) -> None:
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json_body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        payload = self.rfile.read(length)
        return json.loads(payload.decode("utf-8") or "{}")

    def session_token(self) -> str | None:
        header = self.headers.get("Cookie", "")
        jar = cookies.SimpleCookie(header)
        morsel = jar.get(SESSION_COOKIE)
        return morsel.value if morsel else None

    def is_authenticated(self) -> bool:
        if not auth_enabled():
            return True
        return self.session_token() in SESSIONS

    def require_authentication(self) -> bool:
        if self.is_authenticated():
            return True
        self.send_json({"error": "Authentication required."}, status=401)
        return False

    def set_session_cookie(self, token: str) -> None:
        cookie = f"{SESSION_COOKIE}={token}; Path=/; HttpOnly; SameSite=Lax"
        if os.environ.get("RENDER"):
            cookie += "; Secure"
        self.send_header("Set-Cookie", cookie)

    def clear_session_cookie(self) -> None:
        self.send_header(
            "Set-Cookie",
            f"{SESSION_COOKIE}=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax",
        )

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

        if request_path == "/api/auth/status":
            self.send_json({
                "authEnabled": auth_enabled(),
                "authenticated": self.is_authenticated(),
            })
            return

        if request_path == "/api/settings":
            if not self.require_authentication():
                return
            if not SETTINGS_PATH.exists():
                self.send_json({})
                return

            with SETTINGS_PATH.open("r", encoding="utf-8") as file:
                self.send_json(json.load(file))
            return

        if request_path == "/api/quests":
            if not self.require_authentication():
                return
            if not QUESTS_PATH.exists():
                self.send_json([])
                return

            with QUESTS_PATH.open("r", encoding="utf-8") as file:
                self.send_json(json.load(file))
            return

        if auth_enabled() and request_path.startswith("/data/"):
            self.send_json({"error": "Authentication required."}, status=401)
            return

        super().do_GET()

    def do_POST(self) -> None:
        request_path = urlparse(self.path).path

        if request_path == "/api/auth/login":
            try:
                credentials = self.read_json_body()
            except json.JSONDecodeError:
                self.send_json({"error": "Invalid JSON payload."}, status=400)
                return

            expected_user = os.environ.get("APP_USER", "")
            expected_pass = os.environ.get("APP_PASS", "")
            provided_user = str(credentials.get("username", ""))
            provided_pass = str(credentials.get("password", ""))
            valid_login = (
                expected_user
                and expected_pass
                and hmac.compare_digest(provided_user, expected_user)
                and hmac.compare_digest(provided_pass, expected_pass)
            )
            if auth_enabled() and not valid_login:
                self.send_json({"error": "Invalid credentials."}, status=401)
                return

            token = secrets.token_urlsafe(32)
            SESSIONS.add(token)
            body = json.dumps({"ok": True, "authEnabled": auth_enabled()}).encode("utf-8")
            self.send_response(200)
            self.set_session_cookie(token)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if request_path == "/api/auth/logout":
            token = self.session_token()
            if token in SESSIONS:
                SESSIONS.remove(token)
            body = json.dumps({"ok": True}).encode("utf-8")
            self.send_response(200)
            self.clear_session_cookie()
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if request_path != "/api/settings":
            self.send_error(404)
            return

        if not self.require_authentication():
            return

        try:
            settings = self.read_json_body()
        except json.JSONDecodeError:
            self.send_json({"error": "Invalid JSON payload."}, status=400)
            return

        SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with SETTINGS_PATH.open("w", encoding="utf-8") as file:
            json.dump(settings, file, indent=2)
            file.write("\n")

        self.send_json({"ok": True, "settings": settings})


def main() -> None:
    load_env_file()

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
