import os

# Vertex AI Configuration
GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
GCP_LOCATION = os.environ.get("GCP_LOCATION", "us-central1")
# Using gemini-2.5-flash (latest available in your project)
GEMINI_MODEL = "gemini-2.5-flash"

# App metadata
APP_NAME = "AI Travel Planner"
APP_VERSION = "1.0.0"

# Valid options (used for input validation and display)
BUDGET_TYPES = ["budget", "medium", "premium"]
INTEREST_OPTIONS = ["adventure", "food", "nature", "shopping", "culture"]
