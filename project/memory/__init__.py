"""
Pluggable memory for sessions, preferences, and plan history.

Implementations can be added later (SQLite, JSON files, Redis). The protocol
keeps the rest of the codebase decoupled from storage details.
"""

from project.memory.store import MemoryStore, NullMemoryStore
from project.memory.user_memory import JsonUserMemory, UserMemoryState

__all__ = ["MemoryStore", "NullMemoryStore", "JsonUserMemory", "UserMemoryState"]
