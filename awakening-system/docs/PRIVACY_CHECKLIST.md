# Privacy Checklist Before GitHub

Run this checklist before making the repository public.

## Files That Must Not Be Committed

- `.env`
- `data/user_settings.json`
- `__pycache__/`
- `.DS_Store`
- any screenshots showing real email, weight, height, or private settings

## Safe Files To Commit

- `.env.example`
- `data/user_settings.example.json`
- `data/exercises.json`
- source code
- documentation

## Commands

Check ignored private files:

```bash
git check-ignore -v awakening-system/.env awakening-system/data/user_settings.json
```

Search for likely secrets before pushing:

```bash
rg -n "EMAIL_PASS|EMAIL_USER|EMAIL_TO|smtp|password|@" awakening-system --glob '!data/user_settings.json' --glob '!.env'
```

Review staged files before the first commit:

```bash
git status --short
git diff --cached
```

## Public README Rule

Use fake values in examples. Never paste real credentials, real recipient emails, or private SMTP host details into docs or screenshots.
