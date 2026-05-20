"""
Central orchestrator: gathers context from external services, applies deterministic
rules, and delegates itinerary generation to ``itinerary_service``.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from project.agent.decision_engine import build_planning_decision
from project.exceptions import MapsServiceError, WeatherServiceError
from project.memory.user_memory import JsonUserMemory
from project.models.planning_context import AdaptivePlanContext, PlanningDecision
from project.models.user_input import UserInput
from project.services import maps_service, weather_service
from project.utils.route_optimizer import optimize_visit_order

logger = logging.getLogger(__name__)


class TravelAgent:
    """Coordinates weather, maps, routing, decisions, memory, and Gemini prompts."""

    def __init__(self, memory: Optional[JsonUserMemory] = None) -> None:
        self.memory = memory or JsonUserMemory()

    def build_plan_context(self, user_input: UserInput) -> AdaptivePlanContext:
        """Collect structured context for adaptive itinerary prompts."""
        weather: Optional[Dict[str, Any]] = None
        try:
            weather = weather_service.fetch_weather_for_destination(user_input.destination)
        except WeatherServiceError as exc:
            logger.warning("Weather unavailable, continuing without it: %s", exc)

        decision: PlanningDecision = build_planning_decision(user_input, weather)

        attractions: List[Dict[str, Any]] = []
        maps_bundle: Optional[Dict[str, Any]] = None
        optimized: Optional[Dict[str, Any]] = None

        try:
            query = f"top attractions in {user_input.destination}"
            attractions = maps_service.search_places(query, max_results=6)
            if len(attractions) >= 2:
                maps_bundle = maps_service.fetch_route_data_for_attractions(attractions)
                optimized = optimize_visit_order(attractions, maps_bundle["distance_matrix"])
        except MapsServiceError as exc:
            logger.warning("Maps unavailable, continuing without routing hints: %s", exc)

        memory_snapshot = self.memory.to_prompt_snapshot()

        explainability: List[str] = []
        explainability.extend(decision.explanations)
        if optimized and optimized.get("ordered_names"):
            explainability.append(
                "Visit order biased to reduce backtracking using a nearest-neighbor route over driving distances."
            )
        if weather:
            explainability.append(
                "Weather block included live temperature, conditions, and next-day precipitation likelihood."
            )
        if not weather:
            explainability.append("Weather block omitted (missing API key or upstream error); avoid inventing forecasts.")

        return AdaptivePlanContext(
            weather=weather,
            decision=decision,
            maps_route=maps_bundle,
            optimized_route=optimized,
            attractions=attractions,
            memory_snapshot=memory_snapshot,
            explainability=explainability,
        )

    def generate_both_plans(self, user_input: UserInput) -> Dict[str, str]:
        """Produce Budget + Premium markdown itineraries using adaptive prompts."""
        from project.services.itinerary_service import generate_both_plans as gen

        context = self.build_plan_context(user_input)
        return gen(user_input, context)

    def persist_session(self, user_input: UserInput) -> None:
        """Persist lightweight preferences after a successful planning session."""
        food = user_input.preferred_food_type or "any"
        self.memory.merge_from_session(user_input, preferred_food_type=food)
