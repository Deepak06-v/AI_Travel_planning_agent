from models.user_input import UserInput


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
