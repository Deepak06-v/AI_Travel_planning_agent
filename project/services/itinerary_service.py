"""
Itinerary generation: compose prompts and call the Gemini service.

This is the travel-specific orchestration layer. Swap or extend this module
when adding structured outputs, tool use, or replanning without changing the
low-level Vertex client in ``gemini_service``.
"""

import time
from typing import Dict, Optional

from project.models.planning_context import AdaptivePlanContext
from project.models.user_input import UserInput
from project.prompts.itinerary_prompt import build_adaptive_travel_prompt, build_travel_prompt
from project.services.gemini_service import generate_text_completion


def generate_travel_plan(
    user_input: UserInput,
    plan_type: str,
    *,
    context: Optional[AdaptivePlanContext] = None,
) -> str:
    """
    Generate a single travel plan (Budget or Premium variant).

    Args:
        user_input: The user's travel preferences.
        plan_type: "Budget" or "Premium" — controls prompt tone and scope.
        context: Optional adaptive context (weather, routing, rules). When omitted,
            the legacy static prompt is used for backward compatibility.
    """
    if context is None:
        prompt = build_travel_prompt(user_input, plan_type)
    else:
        prompt = build_adaptive_travel_prompt(user_input, plan_type, context)
    return generate_text_completion(
        prompt,
        spinner_message=f"Crafting your {plan_type} travel plan",
    )


def generate_both_plans(
    user_input: UserInput,
    context: Optional[AdaptivePlanContext] = None,
) -> dict:
    """
    Generate both Budget and Premium travel plans sequentially with rate limiting.

    Args:
        user_input: The user's travel preferences.
        context: Optional adaptive planning context. ``None`` keeps the classic prompt.

    Returns:
        Dict with keys "Budget" and "Premium", each containing a plan string.
    """
    plans: dict = {}
    for i, plan_type in enumerate(["Budget", "Premium"]):
        plans[plan_type] = generate_travel_plan(user_input, plan_type, context=context)
        if i < 1:
            time.sleep(1.5)
    return plans
