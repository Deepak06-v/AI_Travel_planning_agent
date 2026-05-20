"""
Deterministic planning rules (no LLM calls).

Consumes structured weather JSON plus ``UserInput`` and emits a ``PlanningDecision``
with concise machine tags and human explanations for downstream prompts.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from project.models.planning_context import PlanningDecision
from project.models.user_input import UserInput

logger = logging.getLogger(__name__)


def _rain_signal(weather: Optional[Dict[str, Any]]) -> bool:
    if not weather:
        return False
    precip = weather.get("precipitation_forecast") or {}
    if precip.get("rain_or_drizzle_expected"):
        return True
    current = weather.get("current") or {}
    condition_main = str((current.get("condition") or {}).get("main", "")).lower()
    return condition_main in {"rain", "drizzle", "thunderstorm"}


def build_planning_decision(
    user_input: UserInput,
    weather: Optional[Dict[str, Any]] = None,
) -> PlanningDecision:
    """
    Apply static rules for adaptive itinerary generation.

    Args:
        user_input: traveler preferences.
        weather: structured payload from ``weather_service.fetch_weather_for_destination`` (optional).

    Returns:
        ``PlanningDecision`` with flags and short explanations (no prose itinerary).
    """
    rain = _rain_signal(weather)
    interests = {i.lower() for i in (user_input.interests or [])}
    budget = (user_input.budget_type or "").lower()

    decision = PlanningDecision()
    explanations: List[str] = []

    if rain:
        decision.prefer_indoor = True
        decision.avoid_beaches = True
        decision.avoid_trekking = True
        decision.tags.extend(["rain_mode", "indoor_bias"])
        pop = (weather or {}).get("precipitation_forecast", {}).get("max_precipitation_probability")
        extra = f" (max POP next 24h: {pop})" if pop is not None else ""
        explanations.append(f"Museum and indoor-friendly stops preferred due to rain forecast{extra}.")
        explanations.append("Beach and trekking-style outdoor blocks should be avoided or replaced.")
    else:
        explanations.append("No strong rain signal in the next day — outdoor pacing is acceptable.")

    if budget == "budget":
        decision.prefer_budget_lodging = True
        decision.minimize_paid_attractions = True
        decision.tags.append("budget_mode")
        explanations.append("Budget tier: favor hostels/guesthouses and low-cost or free activities.")
    elif budget == "medium":
        explanations.append("Mid-range budget: balance comfort and cost without luxury defaults.")
    else:
        explanations.append("Premium budget: quality and comfort can take priority over lowest cost.")

    if "adventure" in interests:
        if rain:
            decision.prefer_active_indoor = True
            decision.tags.append("adventure_indoor")
            explanations.append("Adventure interest noted — prioritize active indoor options while rain persists.")
        else:
            decision.prioritize_outdoor_activities = True
            decision.tags.append("adventure_outdoor")
            explanations.append("Adventure interest: prioritize outdoor/active experiences when weather allows.")

    if "nature" in interests and not rain:
        decision.prioritize_outdoor_activities = True
        decision.tags.append("nature_outdoor")
        explanations.append("Nature interest: include parks/gardens/scenic outdoor time.")

    if "food" in interests:
        decision.tags.append("food_focus")
        explanations.append("Food focus: weave local dining into daily transitions.")

    if "culture" in interests:
        decision.tags.append("culture_focus")
        explanations.append("Culture focus: museums, historic quarters, and local heritage slots.")

    if "shopping" in interests:
        decision.tags.append("shopping_ok")
        explanations.append("Shopping interest: allow markets/boutique districts where practical.")

    decision.explanations = explanations
    logger.debug("Planning decision tags=%s", decision.tags)
    return decision
