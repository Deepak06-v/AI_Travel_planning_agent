#!/usr/bin/env python3
"""
Temporary CLI to exercise OpenWeatherMap integration without running the full planner.

Usage (from repo root):
    set OPENWEATHERMAP_API_KEY=...
    python weather_test_cli.py
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from project.exceptions import WeatherServiceError
from project.logging_config import setup_logging
from project.services.weather_service import fetch_weather_for_destination


def main() -> None:
    setup_logging()
    print("OpenWeatherMap quick test (independent of Gemini / main planner).\n")
    destination = input("Enter destination (e.g. Kyoto, Japan): ").strip()
    if not destination:
        print("Destination required.")
        sys.exit(1)

    try:
        payload = fetch_weather_for_destination(destination)
    except WeatherServiceError as exc:
        print(f"Weather error: {exc}")
        sys.exit(2)

    current = payload.get("current", {})
    precip = payload.get("precipitation_forecast", {})

    print("\n=== Structured JSON ===")
    print(json.dumps(payload, indent=2, ensure_ascii=False))

    print("\n=== Human summary ===")
    print(f"Location: {payload.get('location', {}).get('name')} ({payload.get('location', {}).get('country')})")
    print(f"Temperature (°C): {current.get('temperature_c')}")
    print(f"Condition: {current.get('condition', {}).get('main')} — {current.get('condition', {}).get('description')}")
    print(f"Max rain probability (next ~{precip.get('window_hours')}h): {precip.get('max_precipitation_probability')}")
    print(f"Rain/drizzle likely: {precip.get('rain_or_drizzle_expected')}")


if __name__ == "__main__":
    main()
