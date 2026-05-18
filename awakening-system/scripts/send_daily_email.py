#!/usr/bin/env python3
"""Send the active Daily Quest as a styled HTML email.

Credentials stay in `.env`; personal recipient data comes from
`data/user_settings.json`. The HTML template intentionally uses presentation
tables because email clients often ignore modern layout/background CSS.
"""
from __future__ import annotations

import json
import os
import smtplib
from email.message import EmailMessage
from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUESTS_PATH = ROOT / "data" / "quests.json"
USER_SETTINGS_PATH = ROOT / "data" / "user_settings.json"
ENV_PATH = ROOT / ".env"


def load_env_file(path: Path = ENV_PATH) -> None:
    if not path.exists():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue

        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def env_value(*names: str, default: str | None = None) -> str | None:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return default


def env_flag(*names: str, default: bool = False) -> bool:
    value = env_value(*names)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def load_user_settings() -> dict:
    if not USER_SETTINGS_PATH.exists():
        return {}
    with USER_SETTINGS_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_active_quest() -> dict:
    with QUESTS_PATH.open("r", encoding="utf-8") as file:
        quests = json.load(file)

    if not quests:
        raise SystemExit("No quest found. Run scripts/generate_daily_quest.py first.")
    return quests[0]


def plain_text_body(quest: dict, app_url: str) -> str:
    exercises = "\n".join(
        f"- {exercise['name']}: {exercise['sets']} sets x {exercise['reps']}"
        for exercise in quest["exercises"]
    )
    return (
        f"{quest['title']}\n"
        f"Focus: {quest.get('focus_label', 'Mixed')}\n"
        f"Complete before: {quest['expires_at']}\n\n"
        f"{exercises}\n\n"
        f"Open Awakening System: {app_url}\n"
    )


def html_email_body(quest: dict, app_url: str) -> str:
    exercise_rows = []
    for index, exercise in enumerate(quest["exercises"], start=1):
        tags = "".join(
            f"""
            <span style="display:inline-block;border:1px solid #24516a;border-radius:3px;padding:3px 7px;margin:8px 5px 0 0;color:#55d7ff;font-size:11px;">
              {escape(training_type)}
            </span>
            """
            for training_type in exercise.get("training_types", [])
        )
        exercise_rows.append(
            f"""
            <tr>
              <td style="padding:0 0 12px;">
                <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #244a60;border-radius:6px;background:#0b1e34;">
                  <tr>
                    <td width="42" valign="top" style="padding:15px 0 15px 15px;color:#55d7ff;font-weight:700;">#{index}</td>
                    <td style="padding:15px;">
                      <div style="color:#89a8bc;font-size:12px;margin-bottom:5px;">{escape(exercise['muscle_group'])} / {escape(exercise['equipment'])}</div>
                      <div style="color:#e8f6ff;font-size:18px;font-weight:700;margin-bottom:6px;">{escape(exercise['name'])}</div>
                      <div style="color:#b6cad8;font-size:14px;">{exercise['sets']} sets x {escape(str(exercise['reps']))}</div>
                      <div>{tags}</div>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
            """
        )

    return f"""<!doctype html>
<html style="margin:0;padding:0;background-color:#05070d;background:#05070d;">
  <head>
    <meta charset="utf-8">
    <meta name="color-scheme" content="dark">
    <meta name="supported-color-schemes" content="dark">
    <style>
      html {{
        margin: 0;
        padding: 0;
        background: #05070d;
        background-color: #05070d;
      }}
      body {{
        margin: 0;
        padding: 0;
        background: #05070d;
        background-color: #05070d;
        color: #e8f6ff;
        font-family: Arial, Helvetica, sans-serif;
      }}
    </style>
  </head>
  <body bgcolor="#05070d" style="margin:0;padding:0;background-color:#05070d;background:#05070d;color:#e8f6ff;font-family:Arial,Helvetica,sans-serif;">
    <div style="margin:0;padding:0;background-color:#05070d;background:#05070d;min-height:100%;width:100%;">
      <!--[if mso]>
      <table role="presentation" width="100%" height="100%" cellspacing="0" cellpadding="0" border="0" bgcolor="#05070d"><tr><td bgcolor="#05070d">
      <![endif]-->
      <table role="presentation" width="100%" height="100%" cellspacing="0" cellpadding="0" border="0" bgcolor="#05070d" style="width:100%;min-height:100vh;height:100%;background-color:#05070d;background:#05070d;margin:0;padding:24px;mso-table-lspace:0pt;mso-table-rspace:0pt;">
        <tr>
          <td align="center" valign="top" bgcolor="#05070d" style="background-color:#05070d;background:#05070d;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="#091422" style="max-width:680px;width:100%;border:1px solid #2d6685;background:#091422;background-color:#091422;box-shadow:0 0 30px #0d2b3a;mso-table-lspace:0pt;mso-table-rspace:0pt;">
                <tr>
                  <td style="padding:28px 28px 14px;">
                    <div style="color:#55d7ff;font-size:12px;text-transform:uppercase;margin-bottom:8px;">System Notice</div>
                    <span style="display:inline-block;border:1px solid #244a60;border-radius:3px;padding:4px 8px;color:#89a8bc;background:#0b1e34;font-size:12px;">Active</span>
                    <h1 style="margin:22px 0 10px;color:#e8f6ff;font-size:34px;line-height:1.05;text-shadow:0 0 18px #2d6685;">{escape(quest['title'])}</h1>
                    <p style="margin:0 0 20px;color:#b6cad8;font-size:16px;">Complete the assigned training before the gate closes.</p>
                  </td>
                </tr>
                <tr>
                  <td style="padding:0 28px 18px;">
                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                      <tr>
                        <td style="border:1px solid #21485d;border-radius:6px;background:#0b1e34;padding:14px;">
                          <div style="color:#89a8bc;font-size:12px;margin-bottom:5px;">Focus</div>
                          <div style="color:#e8f6ff;font-size:22px;font-weight:700;">{escape(quest.get('focus_label', 'Mixed'))}</div>
                        </td>
                        <td width="12"></td>
                        <td style="border:1px solid #21485d;border-radius:6px;background:#0b1e34;padding:14px;">
                          <div style="color:#89a8bc;font-size:12px;margin-bottom:5px;">Exercises</div>
                          <div style="color:#e8f6ff;font-size:22px;font-weight:700;">{len(quest['exercises'])}</div>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
                <tr>
                  <td style="padding:0 28px 6px;">
                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                      {''.join(exercise_rows)}
                    </table>
                  </td>
                </tr>
                <tr>
                  <td align="center" style="padding:8px 28px 30px;">
                    <a href="{escape(app_url)}" style="display:inline-block;border:1px solid #55d7ff;border-radius:4px;padding:13px 20px;background:#12324d;color:#55d7ff;text-decoration:none;font-weight:700;text-shadow:0 0 10px #1b5f78;">Open Awakening System</a>
                    <p style="margin:14px 0 0;color:#6f8fa3;font-size:12px;">If this is running locally, keep the dev server active before opening the link.</p>
                  </td>
                </tr>
              </table>
          </td>
        </tr>
      </table>
      <!--[if mso]>
      </td></tr></table>
      <![endif]-->
    </div>
  </body>
</html>"""


def build_email(quest: dict, settings: dict) -> EmailMessage:
    recipient = settings.get("email") or env_value("AWAKENING_EMAIL_TO", "EMAIL_TO")
    sender = env_value("AWAKENING_EMAIL_FROM", "EMAIL_USER")
    app_url = env_value("APP_URL", default="http://127.0.0.1:8001/web/index.html")
    if not recipient or not sender:
        raise SystemExit(
            "Set an email in data/user_settings.json or AWAKENING_EMAIL_TO/EMAIL_TO, "
            "and set AWAKENING_EMAIL_FROM/EMAIL_USER."
        )

    message = EmailMessage()
    message["Subject"] = "Awakening System - Daily Quest Assigned"
    message["From"] = sender
    message["To"] = recipient
    message.set_content(plain_text_body(quest, app_url))
    message.add_alternative(html_email_body(quest, app_url), subtype="html")
    return message


def main() -> None:
    load_env_file()

    if not env_flag("EMAIL_ENABLED", default=True):
        raise SystemExit("EMAIL_ENABLED is false. Enable it before sending.")

    host = env_value("SMTP_HOST", "EMAIL_HOST")
    port = int(env_value("SMTP_PORT", "EMAIL_PORT", default="587"))
    username = env_value("SMTP_USERNAME", "EMAIL_USER")
    password = env_value("SMTP_PASSWORD", "EMAIL_PASS")
    use_tls = env_flag("EMAIL_USE_TLS", default=True)
    use_ssl = env_flag("EMAIL_USE_SSL", default=False)
    if not host or not username or not password:
        raise SystemExit("Set SMTP_HOST/EMAIL_HOST, SMTP_USERNAME/EMAIL_USER, and SMTP_PASSWORD/EMAIL_PASS first.")

    message = build_email(load_active_quest(), load_user_settings())
    smtp_class = smtplib.SMTP_SSL if use_ssl else smtplib.SMTP
    with smtp_class(host, port) as server:
        if use_tls and not use_ssl:
            server.starttls()
        server.login(username, password)
        server.send_message(message)

    print("Daily quest email sent.")


if __name__ == "__main__":
    main()
