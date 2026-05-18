#!/usr/bin/env python3
"""Generate scheduled Daily Quests from local exercise and settings data.

This script is the automation core of the project. It reads a normalized
exercise catalogue, applies the user's local settings, checks weekly rest-day
rules, prevents repeated focus types, and writes the generated quest to JSON.
"""
from __future__ import annotations

import json
import random
from argparse import ArgumentParser
from datetime import date, datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
EXERCISES_PATH = DATA_DIR / "exercises.json"
QUESTS_PATH = DATA_DIR / "quests.json"
USER_SETTINGS_PATH = DATA_DIR / "user_settings.json"
TRAINING_TYPE_LABELS = {
    "arms": "Arms",
    "core": "Core",
    "legs": "Legs",
    "endurance": "Endurance",
    "cardio": "Cardio",
    "strength": "Strength",
}
DEFAULT_SETTINGS = {
    "exercisesPerEmail": 3,
    "timesPerWeek": 4,
    "availableEquipment": ["bodyweight"],
    "trainingPool": ["arms", "core", "legs", "endurance", "cardio", "strength"],
    "workoutStyles": ["strength", "hiit", "conditioning", "mobility", "yoga"],
}
# Weekdays use Python's date.weekday(): Monday=0, Sunday=6.
# The schedules below always leave at least one rest day between emails.
WEEKLY_SCHEDULES = {
    1: [0],
    2: [0, 3],
    3: [0, 2, 4],
    4: [0, 2, 4, 6],
}


def load_json(path: Path, fallback):
    if not path.exists():
        return fallback
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)
        file.write("\n")


def load_user_settings() -> dict:
    saved_settings = load_json(USER_SETTINGS_PATH, {})
    return {**DEFAULT_SETTINGS, **saved_settings}


def week_start_for(day: date) -> date:
    return day - timedelta(days=day.weekday())


def scheduled_weekdays(times_per_week: int) -> list[int]:
    if times_per_week not in WEEKLY_SCHEDULES:
        raise SystemExit(
            "timesPerWeek must be between 1 and 4 when at least one rest day is required "
            "between training emails."
        )
    return WEEKLY_SCHEDULES[times_per_week]


def scheduled_dates_for_week(day: date, times_per_week: int) -> list[date]:
    week_start = week_start_for(day)
    return [week_start + timedelta(days=weekday) for weekday in scheduled_weekdays(times_per_week)]


def session_index_for_day(day: date, times_per_week: int) -> int | None:
    scheduled_dates = scheduled_dates_for_week(day, times_per_week)
    if day not in scheduled_dates:
        return None
    return scheduled_dates.index(day) + 1


def recent_focus_before(quests: list[dict], day: date) -> str | None:
    dated_quests = []
    for quest in quests:
        scheduled_for = quest.get("scheduled_for") or quest.get("issued_at", "")[:10]
        if not scheduled_for:
            continue
        try:
            quest_date = date.fromisoformat(scheduled_for)
        except ValueError:
            continue
        if quest_date < day and quest.get("focus_type"):
            dated_quests.append((quest_date, quest["focus_type"]))

    if not dated_quests:
        return None

    return sorted(dated_quests, key=lambda item: item[0], reverse=True)[0][1]


def exercise_matches_settings(exercise: dict, settings: dict) -> bool:
    equipment = exercise.get("equipment", "").lower()
    available_equipment = {item.lower() for item in settings["availableEquipment"]}
    workout_styles = set(settings["workoutStyles"])

    has_equipment = equipment in available_equipment
    has_style = bool(workout_styles.intersection(exercise.get("workout_styles", [])))
    return has_equipment and has_style


def available_focus_types(exercises: list[dict], quest_size: int, settings: dict) -> list[str]:
    training_pool = set(settings["trainingPool"])
    counts: dict[str, int] = {}
    for exercise in exercises:
        for training_type in exercise.get("training_types", []):
            if training_type in training_pool:
                counts[training_type] = counts.get(training_type, 0) + 1

    return [training_type for training_type, count in counts.items() if count >= quest_size]


def build_daily_quest(
    exercises: list[dict],
    settings: dict,
    quests: list[dict],
    scheduled_for: date,
) -> dict:
    now = datetime.now(timezone.utc)
    eligible_by_settings = [
        exercise for exercise in exercises if exercise_matches_settings(exercise, settings)
    ]
    quest_size = int(settings["exercisesPerEmail"])
    if quest_size <= 0:
        raise SystemExit("Exercises per email must be greater than zero.")

    if len(eligible_by_settings) < quest_size:
        raise SystemExit(
            f"Only {len(eligible_by_settings)} exercises match the current settings; "
            f"{quest_size} are required."
        )

    focus_types = available_focus_types(eligible_by_settings, quest_size, settings)
    if not focus_types:
        raise SystemExit(f"No selected training focus has at least {quest_size} matching exercises.")

    # Avoid hitting the same body focus in consecutive training sessions.
    previous_focus = recent_focus_before(quests, scheduled_for)
    if previous_focus in focus_types:
        focus_types.remove(previous_focus)
    if not focus_types:
        raise SystemExit(
            f"The only available focus is {previous_focus}, which was used in the previous "
            "training session. Add more compatible exercises or broaden your settings."
        )

    focus_type = random.choice(focus_types)
    eligible_exercises = [
        exercise
        for exercise in eligible_by_settings
        if focus_type in exercise.get("training_types", [])
    ]
    quest_exercises = random.sample(eligible_exercises, k=quest_size)
    focus_label = TRAINING_TYPE_LABELS.get(focus_type, focus_type.title())

    return {
        "id": f"quest-{scheduled_for.strftime('%Y%m%d')}",
        "title": f"Daily Quest: {focus_label} Training",
        "status": "active",
        "rank": "E",
        "focus_type": focus_type,
        "focus_label": focus_label,
        "scheduled_for": scheduled_for.isoformat(),
        "week_start": week_start_for(scheduled_for).isoformat(),
        "weekly_session_index": session_index_for_day(
            scheduled_for,
            int(settings["timesPerWeek"]),
        ),
        "times_per_week": int(settings["timesPerWeek"]),
        "issued_at": now.isoformat(),
        "expires_at": (now + timedelta(hours=24)).isoformat(),
        "exercises": quest_exercises,
    }


def main() -> None:
    parser = ArgumentParser(description="Generate the next scheduled Awakening System quest.")
    parser.add_argument("--force", action="store_true", help="Generate a quest even on a rest day.")
    parser.add_argument("--date", help="Generate for a specific date in YYYY-MM-DD format.")
    args = parser.parse_args()

    exercises = load_json(EXERCISES_PATH, [])
    settings = load_user_settings()
    if not exercises:
        raise SystemExit("No exercises found in data/exercises.json")

    scheduled_for = date.fromisoformat(args.date) if args.date else datetime.now().date()
    times_per_week = int(settings["timesPerWeek"])
    session_index = session_index_for_day(scheduled_for, times_per_week)
    if session_index is None and not args.force:
        scheduled_dates = ", ".join(
            day.isoformat() for day in scheduled_dates_for_week(scheduled_for, times_per_week)
        )
        print(
            f"{scheduled_for.isoformat()} is a rest day. Scheduled training days this week: "
            f"{scheduled_dates}."
        )
        return

    quests = load_json(QUESTS_PATH, [])
    today_id = f"quest-{scheduled_for.strftime('%Y%m%d')}"
    quests = [quest for quest in quests if quest.get("id") != today_id]
    quests.insert(0, build_daily_quest(exercises, settings, quests, scheduled_for))
    save_json(QUESTS_PATH, quests)

    quest = quests[0]
    print(
        f"Generated {today_id} with {len(quest['exercises'])} "
        f"{quest['focus_label'].lower()} exercises."
    )


if __name__ == "__main__":
    main()
