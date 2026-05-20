"""
Structured planning context shared between the decision engine, services, and prompts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PlanningDecision:
    """Rule-based constraints derived from weather, budget, and interests."""

    prefer_indoor: bool = False
    avoid_beaches: bool = False
    avoid_trekking: bool = False
    prefer_budget_lodging: bool = False
    minimize_paid_attractions: bool = False
    prioritize_outdoor_activities: bool = False
    prefer_active_indoor: bool = False
    tags: List[str] = field(default_factory=list)
    explanations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prefer_indoor": self.prefer_indoor,
            "avoid_beaches": self.avoid_beaches,
            "avoid_trekking": self.avoid_trekking,
            "prefer_budget_lodging": self.prefer_budget_lodging,
            "minimize_paid_attractions": self.minimize_paid_attractions,
            "prioritize_outdoor_activities": self.prioritize_outdoor_activities,
            "prefer_active_indoor": self.prefer_active_indoor,
            "tags": list(self.tags),
            "explanations": list(self.explanations),
        }


@dataclass
class AdaptivePlanContext:
    """Everything the adaptive itinerary prompt needs beyond raw ``UserInput``."""

    weather: Optional[Dict[str, Any]] = None
    decision: Optional[PlanningDecision] = None
    maps_route: Optional[Dict[str, Any]] = None
    optimized_route: Optional[Dict[str, Any]] = None
    attractions: List[Dict[str, Any]] = field(default_factory=list)
    memory_snapshot: Dict[str, Any] = field(default_factory=dict)
    explainability: List[str] = field(default_factory=list)

    def to_prompt_dict(self) -> Dict[str, Any]:
        return {
            "weather": self.weather,
            "decision": self.decision.to_dict() if self.decision else None,
            "maps_route": self.maps_route,
            "optimized_route": self.optimized_route,
            "attractions": self.attractions,
            "memory_snapshot": self.memory_snapshot,
            "explainability": list(self.explainability),
        }
