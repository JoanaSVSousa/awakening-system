#!/usr/bin/env python3
"""Responsible scraping placeholder for exercise metadata.

The final scraper should collect metadata with attribution and rate limiting.
It should not redistribute protected images, GIFs, videos, or proprietary media.
"""
from __future__ import annotations

"""
Responsible scraper placeholder.

The final version should collect exercise metadata only, keep source attribution,
respect robots.txt and terms, apply rate limiting, and avoid redistributing media
files unless permission or an official API license allows it.
"""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "data" / "scraped_exercises.example.json"


def main() -> None:
    sample_record = {
        "name": "Example Exercise",
        "muscle_group": "example",
        "difficulty": "beginner",
        "equipment": "bodyweight",
        "instructions": [],
        "source": "Example source",
        "source_url": "https://example.com/exercises/example",
        "demo_url": "",
    }

    OUTPUT_PATH.write_text(json.dumps([sample_record], indent=2) + "\n", encoding="utf-8")
    print(f"Wrote example scraper output to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

