"""Application settings, model name, and environment-driven configuration."""

import os
from pathlib import Path

# Vertex AI Configuration
GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
GCP_LOCATION = os.environ.get("GCP_LOCATION", "us-central1")
# Using gemini-2.5-flash (latest available in your project)
GEMINI_MODEL = "gemini-2.5-flash"

# OpenWeatherMap
OPENWEATHERMAP_API_KEY = os.environ.get("OPENWEATHERMAP_API_KEY")
OPENWEATHER_TIMEOUT_SECONDS = float(os.environ.get("OPENWEATHER_TIMEOUT_SECONDS", "15"))

# Google Maps (Distance Matrix + Places)
GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")
GOOGLE_MAPS_TIMEOUT_SECONDS = float(os.environ.get("GOOGLE_MAPS_TIMEOUT_SECONDS", "15"))

# JSON user memory (lightweight persistence)
DEFAULT_MEMORY_PATH = Path.home() / ".travel_planner_user_memory.json"
USER_MEMORY_PATH = Path(os.environ.get("TRAVEL_PLANNER_MEMORY_PATH", str(DEFAULT_MEMORY_PATH)))

# App metadata
APP_NAME = "AI Travel Planner"
APP_VERSION = "1.0.0"

# Valid options (used for input validation and display)
BUDGET_TYPES = ["budget", "medium", "premium"]
INTEREST_OPTIONS = ["adventure", "food", "nature", "shopping", "culture"]
FOOD_TYPE_OPTIONS = ["any", "local", "vegetarian", "vegan", "halal", "seafood", "street_food"]
