from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class UserInput:
    """Represents the collected travel preferences from the user."""

    destination: str
    travel_days: int
    budget_type: str  # "budget", "medium", or "premium"
    interests: List[str] = field(default_factory=list)
    preferred_food_type: Optional[str] = None

    def summary(self) -> str:
        """Return a human-readable summary of user preferences."""
        interests_str = ", ".join(self.interests) if self.interests else "general sightseeing"
        food = self.preferred_food_type or "any"
        return (
            f"Destination: {self.destination}\n"
            f"Duration: {self.travel_days} day(s)\n"
            f"Budget Type: {self.budget_type.capitalize()}\n"
            f"Interests: {interests_str}\n"
            f"Food preference: {food}"
        )
