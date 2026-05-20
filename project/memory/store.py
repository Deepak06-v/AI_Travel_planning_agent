"""Abstract memory boundary for future persistence."""

from typing import Any, Dict, Optional, Protocol, runtime_checkable


@runtime_checkable
class MemoryStore(Protocol):
    """Minimal contract for trip/session memory (to be implemented later)."""

    def save_session(self, session_id: str, payload: Dict[str, Any]) -> None:
        """Persist arbitrary session-scoped data."""
        ...

    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load session data if present."""
        ...


class NullMemoryStore:
    """No-op store: keeps imports and type checks working before real storage exists."""

    def save_session(self, session_id: str, payload: Dict[str, Any]) -> None:
        return None

    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        return None
