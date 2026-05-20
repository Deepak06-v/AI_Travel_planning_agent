"""
Google Maps client helpers (Places Text Search + Distance Matrix).

Returns structured JSON-serializable dicts. Route optimization lives in
``project.utils.route_optimizer`` — this module only fetches distances/times
and resolves places.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Sequence, Tuple

import requests

from project.config import GOOGLE_MAPS_API_KEY, GOOGLE_MAPS_TIMEOUT_SECONDS
from project.exceptions import MapsServiceError

logger = logging.getLogger(__name__)

PLACES_TEXT_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
DISTANCE_MATRIX_URL = "https://maps.googleapis.com/maps/api/distancematrix/json"


def _require_api_key() -> str:
    if not GOOGLE_MAPS_API_KEY:
        raise MapsServiceError(
            "GOOGLE_MAPS_API_KEY is not set. Export it before calling Google Maps services."
        )
    return GOOGLE_MAPS_API_KEY


def _get_json(url: str, params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        response = requests.get(url, params=params, timeout=GOOGLE_MAPS_TIMEOUT_SECONDS)
    except requests.RequestException as exc:
        logger.exception("Google Maps request failed: %s", url)
        raise MapsServiceError(f"Maps request failed: {exc}") from exc

    try:
        payload = response.json()
    except ValueError as exc:
        raise MapsServiceError("Google Maps returned invalid JSON.") from exc

    status = payload.get("status")
    if response.status_code != 200 or status not in {"OK", "ZERO_RESULTS"}:
        logger.error("Google Maps error | HTTP %s | status=%s | body=%s", response.status_code, status, str(payload)[:500])
        error_message = payload.get("error_message") or status or "UNKNOWN_ERROR"
        raise MapsServiceError(f"Google Maps API error: {error_message}")

    return payload


def search_places(query: str, *, max_results: int = 8) -> List[Dict[str, Any]]:
    """
    Text search for places near a free-text query.

    Returns a list of dicts with ``name``, ``place_id``, ``latitude``, ``longitude``.
    """
    key = _require_api_key()
    trimmed = (query or "").strip()
    if not trimmed:
        raise MapsServiceError("Place search query must be non-empty.")

    payload = _get_json(
        PLACES_TEXT_SEARCH_URL,
        {"query": trimmed, "key": key},
    )

    results: List[Dict[str, Any]] = []
    for raw in (payload.get("results") or [])[:max_results]:
        geometry = raw.get("geometry") or {}
        loc = geometry.get("location") or {}
        results.append(
            {
                "name": raw.get("name"),
                "place_id": raw.get("place_id"),
                "formatted_address": raw.get("formatted_address"),
                "latitude": float(loc.get("lat", 0.0) or 0.0),
                "longitude": float(loc.get("lng", 0.0) or 0.0),
            }
        )

    logger.info("Places text search returned %s results for query=%r", len(results), trimmed)
    return results


def _format_lat_lng(lat: float, lng: float) -> str:
    return f"{lat},{lng}"


def distance_matrix(
    origins: Sequence[Tuple[float, float]],
    destinations: Sequence[Tuple[float, float]],
    *,
    mode: str = "driving",
) -> Dict[str, Any]:
    """
    Call the Distance Matrix API.

    Args:
        origins: sequence of (lat, lng)
        destinations: sequence of (lat, lng)
        mode: travel mode supported by the API (driving, walking, bicycling, transit)

    Returns:
        Structured dict:

        .. code-block:: json

            {
              "origin_count": n,
              "destination_count": m,
              "rows": [
                {
                  "origin_index": 0,
                  "elements": [
                    {
                      "destination_index": 0,
                      "status": "OK",
                      "distance_meters": 1200,
                      "duration_seconds": 600
                    }
                  ]
                }
              ]
            }
    """
    key = _require_api_key()
    if not origins or not destinations:
        raise MapsServiceError("Origins and destinations must be non-empty sequences.")

    origins_param = "|".join(_format_lat_lng(lat, lng) for lat, lng in origins)
    destinations_param = "|".join(_format_lat_lng(lat, lng) for lat, lng in destinations)

    payload = _get_json(
        DISTANCE_MATRIX_URL,
        {
            "origins": origins_param,
            "destinations": destinations_param,
            "mode": mode,
            "units": "metric",
            "key": key,
        },
    )

    rows_out: List[Dict[str, Any]] = []
    for r_idx, row in enumerate(payload.get("rows") or []):
        elements_out: List[Dict[str, Any]] = []
        for c_idx, element in enumerate(row.get("elements") or []):
            entry: Dict[str, Any] = {
                "destination_index": c_idx,
                "status": element.get("status"),
            }
            distance = element.get("distance") or {}
            duration = element.get("duration") or {}
            if element.get("status") == "OK":
                entry["distance_meters"] = int(distance.get("value", 0) or 0)
                entry["duration_seconds"] = int(duration.get("value", 0) or 0)
            elements_out.append(entry)
        rows_out.append({"origin_index": r_idx, "elements": elements_out})

    structured = {
        "provider": "google_maps_distance_matrix",
        "travel_mode": mode,
        "origin_count": len(origins),
        "destination_count": len(destinations),
        "rows": rows_out,
    }
    logger.info(
        "Distance matrix computed | origins=%s destinations=%s mode=%s",
        len(origins),
        len(destinations),
        mode,
    )
    return structured


def fetch_route_data_for_attractions(places: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Convenience: build a full origin-destination matrix for the given places.

    ``places`` entries must include ``latitude`` and ``longitude``.
    """
    coords = [(float(p["latitude"]), float(p["longitude"])) for p in places]
    matrix = distance_matrix(coords, coords)
    return {
        "places": list(places),
        "distance_matrix": matrix,
    }
