"""
OpenWeatherMap integration: current conditions + short-range precipitation signal.

Returns a structured JSON-serializable dict (no ORM objects) suitable for the
decision engine and Gemini context blocks.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import requests

from project.config import OPENWEATHERMAP_API_KEY, OPENWEATHER_TIMEOUT_SECONDS
from project.exceptions import WeatherServiceError

logger = logging.getLogger(__name__)

OWM_CURRENT_URL = "https://api.openweathermap.org/data/2.5/weather"
OWM_FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"


def _require_api_key() -> str:
    if not OPENWEATHERMAP_API_KEY:
        raise WeatherServiceError(
            "OPENWEATHERMAP_API_KEY is not set. Export it in your environment before calling the weather service."
        )
    return OPENWEATHERMAP_API_KEY


def _get_json(url: str, params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        response = requests.get(url, params=params, timeout=OPENWEATHER_TIMEOUT_SECONDS)
    except requests.RequestException as exc:
        logger.exception("OpenWeatherMap request failed: %s", url)
        raise WeatherServiceError(f"Weather request failed: {exc}") from exc

    if response.status_code != 200:
        logger.error("OpenWeatherMap HTTP %s: %s", response.status_code, response.text[:500])
        raise WeatherServiceError(
            f"OpenWeatherMap returned HTTP {response.status_code}. "
            "Check the destination spelling and API key permissions."
        )

    try:
        return response.json()
    except ValueError as exc:
        logger.error("OpenWeatherMap returned non-JSON body")
        raise WeatherServiceError("OpenWeatherMap returned an invalid JSON payload.") from exc


def _normalize_current(payload: Dict[str, Any]) -> Dict[str, Any]:
    main = payload.get("main") or {}
    weather = (payload.get("weather") or [{}])[0]
    return {
        "temperature_c": round(float(main.get("temp", 0.0)), 2),
        "feels_like_c": round(float(main.get("feels_like", 0.0)), 2),
        "humidity_percent": int(main.get("humidity", 0) or 0),
        "condition": {
            "id": int(weather.get("id", 0) or 0),
            "main": str(weather.get("main", "")),
            "description": str(weather.get("description", "")),
        },
    }


def _normalize_forecast_slice(entries: List[Dict[str, Any]], hours: int = 24) -> Dict[str, Any]:
    """
    Use the next ``hours`` hours of 3-hour forecast steps (default 24h ≈ 8 steps).
    ``pop`` is probability of precipitation (0..1).
    """
    steps = max(1, min(len(entries), (hours + 2) // 3))
    selected = entries[:steps]
    pops = [float(item.get("pop", 0.0) or 0.0) for item in selected]
    max_pop = max(pops) if pops else 0.0
    rain_like = any(
        str((item.get("weather") or [{}])[0].get("main", "")).lower() in {"rain", "drizzle", "thunderstorm"}
        for item in selected
    )
    return {
        "window_hours": hours,
        "samples": steps,
        "max_precipitation_probability": round(max_pop, 3),
        "rain_or_drizzle_expected": bool(rain_like or max_pop >= 0.35),
    }


def fetch_weather_for_destination(destination_query: str) -> Dict[str, Any]:
    """
    Fetch structured weather for a free-text destination (city, region, etc.).

    Args:
        destination_query: Human destination string, e.g. "Kyoto, Japan".

    Returns:
        JSON-serializable dict with location, current conditions, and precipitation outlook.

    Raises:
        WeatherServiceError: configuration, transport, or API errors.
    """
    key = _require_api_key()
    trimmed = (destination_query or "").strip()
    if not trimmed:
        raise WeatherServiceError("Destination query must be a non-empty string.")

    common = {"q": trimmed, "appid": key, "units": "metric"}

    current_raw = _get_json(OWM_CURRENT_URL, common)
    forecast_raw = _get_json(OWM_FORECAST_URL, common)

    coord = current_raw.get("coord") or {}
    location_block = {
        "query": trimmed,
        "name": current_raw.get("name"),
        "country": current_raw.get("sys", {}).get("country"),
        "latitude": float(coord.get("lat", 0.0) or 0.0),
        "longitude": float(coord.get("lon", 0.0) or 0.0),
    }

    forecast_list = forecast_raw.get("list") or []
    forecast_summary = _normalize_forecast_slice(forecast_list, hours=24)

    result: Dict[str, Any] = {
        "provider": "openweathermap",
        "location": location_block,
        "current": _normalize_current(current_raw),
        "precipitation_forecast": forecast_summary,
    }

    logger.info(
        "Weather fetched for %s | temp_c=%s | max_pop=%s",
        trimmed,
        result["current"]["temperature_c"],
        forecast_summary["max_precipitation_probability"],
    )
    return result
