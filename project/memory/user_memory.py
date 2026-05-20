"""
JSON-backed user memory for lightweight personalization across sessions.

Stores preferences and light history — no database required. File path is
configurable via ``TRAVEL_PLANNER_MEMORY_PATH`` (defaults to ``~/.travel_planner_user_memory.json``).
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from project.config import USER_MEMORY_PATH
from project.models.user_input import UserInput

logger = logging.getLogger(__name__)


@dataclass
class UserMemoryState:
    preferred_budget: Optional[str] = None
    travel_interests: List[str] = field(default_factory=list)
    preferred_food_type: Optional[str] = None
    past_destinations: List[str] = field(default_factory=list)

    @staticmethod
    def from_dict(payload: Dict[str, Any]) -> "UserMemoryState":
        return UserMemoryState(
            preferred_budget=payload.get("preferred_budget"),
            travel_interests=list(payload.get("travel_interests") or []),
            preferred_food_type=payload.get("preferred_food_type"),
            past_destinations=list(payload.get("past_destinations") or []),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "preferred_budget": self.preferred_budget,
            "travel_interests": list(self.travel_interests),
            "preferred_food_type": self.preferred_food_type,
            "past_destinations": list(self.past_destinations),
        }


class JsonUserMemory:
    """Load/save ``UserMemoryState`` to disk as JSON."""

    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = Path(path or USER_MEMORY_PATH)

    def load(self) -> UserMemoryState:
        if not self.path.exists():
            logger.info("No memory file at %s — starting fresh.", self.path)
            return UserMemoryState()

        try:
            raw_text = self.path.read_text(encoding="utf-8")
            payload = json.loads(raw_text)
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Failed to read memory file (%s): %s", self.path, exc)
            return UserMemoryState()

        try:
            return UserMemoryState.from_dict(payload)
        except (TypeError, ValueError) as exc:
            logger.warning("Malformed memory payload — resetting. Error: %s", exc)
            return UserMemoryState()

    def save(self, state: UserMemoryState) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.path.with_suffix(self.path.suffix + ".tmp")
        data = json.dumps(state.to_dict(), indent=2, ensure_ascii=False)
        tmp_path.write_text(data, encoding="utf-8")
        tmp_path.replace(self.path)
        logger.info("Saved user memory to %s", self.path)

    def merge_from_session(self, user_input: UserInput, *, preferred_food_type: Optional[str]) -> UserMemoryState:
        """Update stored preferences using the latest successful session."""
        state = self.load()
        state.preferred_budget = user_input.budget_type
        state.travel_interests = list(user_input.interests or [])
        state.preferred_food_type = preferred_food_type

        dest = (user_input.destination or "").strip()
        if dest:
            history = [d for d in state.past_destinations if d.lower() != dest.lower()]
            history.insert(0, dest)
            state.past_destinations = history[:25]

        self.save(state)
        return state

    def to_prompt_snapshot(self, state: Optional[UserMemoryState] = None) -> Dict[str, Any]:
        """Compact dict for LLM context (not a full user profile dump)."""
        snapshot = state or self.load()
        return {
            "preferred_budget": snapshot.preferred_budget,
            "travel_interests": snapshot.travel_interests,
            "preferred_food_type": snapshot.preferred_food_type,
            "recent_destinations": snapshot.past_destinations[:5],
        }
