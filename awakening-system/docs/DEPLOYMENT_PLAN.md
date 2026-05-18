# Deployment Plan

The project should have two versions: a public sandbox and a private production-like version.

## Public Sandbox

Goal: safe GitHub/LinkedIn demo.

Keep:

- seed exercise data;
- demo login;
- localStorage progress;
- example settings;
- email preview/sender code;
- documentation.

Do not include:

- `.env`;
- real email addresses;
- real SMTP passwords;
- real weight/height/settings;
- private generated history if it reveals personal behavior.

## Private Version

Goal: actual use with login, persisted profile, scheduled email delivery, and history.

Recommended stack:

- Render Web Service for the Python app/API.
- Render Cron Job for scheduled quest generation and email sending.
- Supabase Auth for login.
- Supabase Postgres for users, settings, quests, progress, and attributes.
- Render environment variables for SMTP credentials and Supabase service keys.

## Suggested Supabase Tables

```txt
profiles
  id uuid primary key references auth.users
  email text
  display_name text
  created_at timestamptz

user_settings
  user_id uuid references profiles
  exercises_per_email int
  times_per_week int
  weight_kg numeric nullable
  height_cm numeric nullable
  available_equipment text[]
  training_pool text[]
  workout_styles text[]

quests
  id uuid primary key
  user_id uuid references profiles
  focus_type text
  focus_label text
  scheduled_for date
  issued_at timestamptz
  expires_at timestamptz
  status text

quest_exercises
  quest_id uuid references quests
  exercise_id text
  position int
  sets int
  reps text

attributes
  user_id uuid references profiles
  arms int
  core int
  legs int
  endurance int
  cardio int
  strength int
```

## Auth Migration

Replace the sandbox login in `web/app.js` with Supabase Auth. The public anon key can be used in the frontend, but service-role keys must stay server-side only.

## Time Remaining In Production

Store `issued_at` and `expires_at` in UTC. Render/Supabase should calculate or persist the timestamps. The browser displays the countdown from `expires_at`.

## Cron Strategy

A Render Cron Job can run once per day:

```bash
python3 scripts/generate_daily_quest.py && python3 scripts/send_daily_email.py
```

For multiple users, this should become a server-side job that queries users whose schedule includes today, generates each quest, and sends each email.
