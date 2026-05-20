"""
Travel planner application package.

All runtime modules live under ``project`` so imports stay explicit
(``from project.services.itinerary_service import generate_both_plans``).
"""

from project.config import APP_NAME, APP_VERSION

__all__ = ["APP_NAME", "APP_VERSION"]
