import json

from project.models.planning_context import AdaptivePlanContext
from project.models.user_input import UserInput


def build_travel_prompt(user_input: UserInput, plan_type: str) -> str:
    """
    Build a detailed prompt for the Gemini API based on user preferences.

    Args:
        user_input: The collected user travel preferences.
        plan_type: Either "Budget" or "Premium" to indicate which plan to generate.

    Returns:
        A formatted prompt string ready to send to Gemini.
    """
    interests_str = ", ".join(user_input.interests) if user_input.interests else "general tourism"
    food_line = ""
    if user_input.preferred_food_type:
        food_line = f"- Food preference: {user_input.preferred_food_type}\n"

    # Adjust tone and scope based on plan type
    if plan_type == "Budget":
        budget_guidance = (
            "Focus on affordable accommodations (hostels, budget hotels, guesthouses), "
            "local street food and cheap eats, free or low-cost attractions, and "
            "public transport options. Keep total estimated cost as low as reasonably possible."
        )
    else:
        budget_guidance = (
            "Focus on premium accommodations (4-5 star hotels, boutique stays), "
            "fine dining and signature restaurants, exclusive experiences, private tours, "
            "and premium transport options. Price is not a constraint — prioritize quality and comfort."
        )

    prompt = f"""You are an expert travel planner with decades of experience crafting personalized itineraries worldwide.

A traveler has requested a {plan_type} travel plan with the following preferences:
- Destination: {user_input.destination}
- Duration: {user_input.travel_days} days
- Interests: {interests_str}
- Budget Type: {user_input.budget_type.capitalize()} (generating {plan_type} plan)
{food_line}
{budget_guidance}

Please generate a detailed, realistic, and actionable travel itinerary that includes:

1. **OVERVIEW**
   - Brief introduction to the destination
   - Best time to visit (if applicable)
   - Key highlights of this plan

2. **DAY-WISE ITINERARY**
   For each day (Day 1 through Day {user_input.travel_days}):
   - Morning, Afternoon, and Evening activities
   - Specific places to visit with brief descriptions
   - Estimated time at each location
   - Transportation between locations

3. **HOTEL SUGGESTIONS**
   - 2-3 recommended accommodations matching the {plan_type} budget
   - Include neighborhood, price range per night, and key amenities

4. **FOOD RECOMMENDATIONS**
   - Must-try local dishes
   - 3-5 recommended restaurants or food spots matching the budget
   - Any food experiences tied to the traveler's interests

5. **APPROXIMATE BUDGET BREAKDOWN**
   - Accommodation (total for {user_input.travel_days} nights)
   - Food & Dining (per day estimate)
   - Activities & Entrance Fees
   - Local Transportation
   - Miscellaneous & Shopping
   - **TOTAL ESTIMATED COST** (in USD)

6. **TRAVEL TIPS**
   - 4-6 practical tips specific to this destination
   - Cultural etiquette or important local customs
   - Safety considerations if relevant
   - Packing suggestions based on activities

Make the itinerary engaging, practical, and tailored to the traveler's interests in {interests_str}.
Use clear headings, bullet points, and organized sections. Be specific with place names, not generic.
"""
    return prompt


def _compact_context_for_prompt(context: AdaptivePlanContext) -> dict:
    """Trim heavy fields before embedding JSON in the LLM prompt."""
    weather = context.weather
    decision = context.decision.to_dict() if context.decision else None
    optimized = context.optimized_route
    maps_route = context.maps_route
    attractions = [
        {
            "name": item.get("name"),
            "latitude": item.get("latitude"),
            "longitude": item.get("longitude"),
        }
        for item in (context.attractions or [])[:8]
    ]
    return {
        "weather": weather,
        "planning_decision": decision,
        "optimized_route": optimized,
        "maps_distance_matrix_meta": {
            "origin_count": (maps_route or {}).get("distance_matrix", {}).get("origin_count"),
            "destination_count": (maps_route or {}).get("distance_matrix", {}).get("destination_count"),
        }
        if maps_route
        else None,
        "candidate_attractions": attractions,
        "memory_snapshot": context.memory_snapshot,
        "explainability": context.explainability,
    }


def build_adaptive_travel_prompt(user_input: UserInput, plan_type: str, context: AdaptivePlanContext) -> str:
    """
    Build a prompt that injects structured agent context (weather, rules, routes, memory).

    The model must respect ``planning_decision`` flags and briefly cite why major choices
    differ from a generic itinerary (concise ``ADAPTATION NOTES`` section).
    """
    interests_str = ", ".join(user_input.interests) if user_input.interests else "general tourism"
    food_line = ""
    if user_input.preferred_food_type:
        food_line = f"- Food preference: {user_input.preferred_food_type}\n"

    if plan_type == "Budget":
        budget_guidance = (
            "Focus on affordable accommodations (hostels, budget hotels, guesthouses), "
            "local street food and cheap eats, free or low-cost attractions, and "
            "public transport options. Keep total estimated cost as low as reasonably possible."
        )
    else:
        budget_guidance = (
            "Focus on premium accommodations (4-5 star hotels, boutique stays), "
            "fine dining and signature restaurants, exclusive experiences, private tours, "
            "and premium transport options. Price is not a constraint — prioritize quality and comfort."
        )

    structured = _compact_context_for_prompt(context)
    structured_json = json.dumps(structured, ensure_ascii=False, indent=2)

    prompt = f"""You are an adaptive travel planner. Use the STRUCTURED_CONTEXT JSON as hard guidance.
Honor ``planning_decision`` flags literally (indoor bias, avoid beaches/trekking, budget lodging, etc.).
Keep wording concise and actionable — avoid long essays or duplicate tips.

STRUCTURED_CONTEXT:
```json
{structured_json}
```

Traveler request summary:
- Destination: {user_input.destination}
- Duration: {user_input.travel_days} days
- Interests: {interests_str}
- Budget Type: {user_input.budget_type.capitalize()} (tone for this document: {plan_type} plan)
{food_line}
{budget_guidance}

Output sections (use markdown headings):
1. **OVERVIEW** — 3-5 bullets max.
2. **DAY-WISE ITINERARY** — For each day: morning / afternoon / evening. Mention realistic travel times.
   - If ``optimized_route.ordered_names`` exists, bias day ordering toward that sequence when it makes geographic sense.
   - If weather JSON is missing, proceed without inventing fake forecasts.
3. **HOTEL SUGGESTIONS** — 2-3 picks aligned with budget + decision flags.
4. **FOOD RECOMMENDATIONS** — 3-5 picks; respect stored food preference when provided.
5. **BUDGET BREAKDOWN** — compact USD table-style bullets.
6. **TRAVEL TIPS** — max 6 bullets, highly specific to the destination.
7. **ADAPTATION NOTES** — 3-5 short bullets explaining *why* you shaped the plan (e.g., rain → indoor swaps,
   budget flags → cheaper picks, optimized route → less backtracking). Use the explainability lines as seeds, not copy-paste.

Tone: confident, practical, non-marketing. Prefer real venue/area names; if unknown, say "TBD on-site" rather than fabricating.
"""
    return prompt
