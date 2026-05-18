# Presentation Guide

Use this as your speaking guide for LinkedIn, GitHub, or recruiter conversations.

## One-Sentence Pitch

Awakening System is a Python and vanilla JavaScript app that generates personalized 24-hour workout quests, emails them to the user, and tracks completion through an RPG-style interface.

## What To Show First

1. Open the app and log into the sandbox.
2. Show the Daily Quest title, focus, countdown, and exercises.
3. Open settings and explain equipment/style filtering.
4. Press Play in the Quest Timer and show the audio cue and active card.
5. Open Rank E and show the radar chart.
6. Mention that email sending works through SMTP but secrets are kept private.

## Technical Talking Points

- The app uses `exercises.json` as a normalized exercise database.
- Every exercise can belong to multiple focus types.
- The generator chooses one common focus per Daily Quest.
- Weekly scheduling respects rest days and avoids repeating the previous focus.
- The countdown is derived from `expires_at`, not hardcoded UI state.
- The email template uses email-safe HTML tables because many email clients ignore modern CSS.
- The frontend uses Web Audio API for timer cues without audio files.
- Private config is excluded from GitHub through `.gitignore`.

## How To Explain The Sandbox Login

The current login gate is intentionally a sandbox/demo login. It is there to demonstrate user flow without exposing real authentication keys. In the private/deployed version, it should be replaced by Supabase Auth.

## Portfolio Framing

Good LinkedIn phrasing:

> I built Awakening System, a local-first Python and vanilla JS project that turns exercise data into scheduled Daily Quests, sends styled quest emails, and tracks progress with a timer and RPG-like attribute system. I focused on automation, data modeling, privacy-safe configuration, and responsible scraping design.

## Interview Questions You Can Answer

**Why JSON files instead of a database?**

Because the sandbox version is meant to be inspectable and framework-free. The data model is simple, and JSON makes it easy to show how the automation works. The migration path is Supabase Postgres.

**How do you avoid sending unsafe/private data to GitHub?**

Secrets live in `.env`; personal settings live in `data/user_settings.json`; both are ignored. GitHub only gets examples.

**How does the generator avoid random messy workouts?**

It filters compatible exercises, picks a shared focus, and then samples only exercises that match that focus.

**How does the timer know what is timed?**

It parses `reps` text for `sec` or `min`. Timed exercises count down automatically; rep-based exercises are manual and advanced with Next.
