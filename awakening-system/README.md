# Awakening System

Awakening System is a local-first daily training quest app built with Python scripts and vanilla HTML, CSS, and JavaScript. It turns a workout plan into a 24-hour RPG-style quest, sends the quest by email, and tracks completion through a sci-fi system interface.

This project is intentionally framework-free while learning. It focuses on scripting, data normalization, email automation, scheduling rules, local storage, and a polished interface suitable for a portfolio demo.

## What It Demonstrates

- Python scripting for quest generation, weekly scheduling, and email automation.
- JSON data modeling for exercises, user settings, generated quests, and privacy-safe examples.
- Vanilla JavaScript for state, timers, Web Audio cues, settings, a demo login, and a radar chart.
- Responsible scraping design: metadata and attribution, not redistribution of protected media.
- Email templating that works across stricter email clients using table-based dark HTML.
- Privacy hygiene for GitHub: real `.env` and personal settings are ignored.

## Current Features

- Generates Daily Quests with a shared training focus such as `core`, `legs`, `cardio`, or `strength`.
- Filters exercises by equipment, training style, training pool, and exercise count.
- Respects weekly frequency with rest days between training emails.
- Avoids repeating the same focus on consecutive training sessions.
- Sends a styled HTML email with a link back to the app.
- Shows a 24-hour countdown based on the quest `expires_at` timestamp.
- Includes a circuit timer with Play, Next, Reset, rest periods, animated active cards, and audio cues.
- Awards attribute points after quest completion and displays them on a radar chart.
- Provides a sandbox login gate for public demos. This is not production authentication.

## Project Structure

```txt
awakening-system/
  data/
    exercises.json                 # Public exercise catalogue used by the generator
    quests.json                    # Generated quest history for local/demo use
    user_settings.example.json     # Safe settings template for GitHub
    user_settings.json             # Private local settings, ignored by Git
  docs/
    ARCHITECTURE.md
    DEPLOYMENT_PLAN.md
    PRESENTATION_GUIDE.md
    PRIVACY_CHECKLIST.md
  scripts/
    dev_server.py                  # Local static/API server
    generate_daily_quest.py        # Quest generation and scheduling rules
    send_daily_email.py            # SMTP email sender and HTML template
    scrape_exercises.py            # Responsible scraping placeholder
  web/
    index.html
    styles.css
    app.js
```

## Quick Start

Create local private config files from the examples:

```bash
cp .env.example .env
cp data/user_settings.example.json data/user_settings.json
```

Start the local server:

```bash
python3 scripts/dev_server.py
```

Open:

```txt
http://127.0.0.1:8001/web/index.html
```

Generate a quest for today:

```bash
python3 scripts/generate_daily_quest.py
```

Generate a quest for a specific date while testing schedule rules:

```bash
python3 scripts/generate_daily_quest.py --date 2026-05-18
```

Send the current quest by email:

```bash
python3 scripts/send_daily_email.py
```

## Privacy

Do not commit `.env` or `data/user_settings.json`. They are intentionally ignored because they can contain email credentials, email addresses, weight, height, and personal preferences.

Before publishing to GitHub, run through [docs/PRIVACY_CHECKLIST.md](docs/PRIVACY_CHECKLIST.md).

## Sandbox vs Private Version

The public sandbox version should show the product, scripts, data model, and UI without real secrets or personal data. The private version can use Supabase Auth, Supabase Postgres, and Render Cron Jobs to support real login, storage, and scheduled emails. See [docs/DEPLOYMENT_PLAN.md](docs/DEPLOYMENT_PLAN.md).

## Scraping Note

This project treats scraping as a responsible data collection exercise. The scraper is designed to collect public exercise metadata, keep source URLs, use rate limiting, and avoid redistributing protected media assets.

Exercise demonstrations should be linked, embedded with permission, sourced through an official API, or replaced with original project assets.
