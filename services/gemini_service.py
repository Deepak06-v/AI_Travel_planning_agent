import sys
import threading
import time
import random

import vertexai
from vertexai.generative_models import GenerativeModel

from config import GCP_PROJECT_ID, GCP_LOCATION, GEMINI_MODEL
from services.prompt_builder import build_travel_prompt
from models.user_input import UserInput


def _initialize_vertexai():
    """Initialize Vertex AI with project and location."""
    if not GCP_PROJECT_ID:
        raise ValueError(
            "GCP_PROJECT_ID environment variable is not set. "
            "Please set it before running the application."
        )
    
    vertexai.init(project=GCP_PROJECT_ID, location=GCP_LOCATION)


class LoadingSpinner:
    """A simple terminal loading spinner for async visual feedback."""

    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(self, message: str = "Generating your travel plan"):
        self.message = message
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._spin, daemon=True)

    def _spin(self):
        idx = 0
        while not self._stop_event.is_set():
            frame = self.FRAMES[idx % len(self.FRAMES)]
            sys.stdout.write(f"\r  \033[96m{frame}\033[0m  {self.message}... ")
            sys.stdout.flush()
            time.sleep(0.1)
            idx += 1

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        self._thread.join()
        # Clear the spinner line
        sys.stdout.write("\r" + " " * (len(self.message) + 20) + "\r")
        sys.stdout.flush()


def generate_travel_plan(user_input: UserInput, plan_type: str) -> str:
    """
    Generate a single travel plan using Vertex AI with retry logic.

    Args:
        user_input: The user's travel preferences.
        plan_type: "Budget" or "Premium" — controls prompt tone and scope.

    Returns:
        The generated itinerary as a plain string.

    Raises:
        ValueError: If credentials are missing.
        RuntimeError: If the Vertex AI call fails after retries.
    """
    _initialize_vertexai()
    model = GenerativeModel(model_name=GEMINI_MODEL)
    prompt = build_travel_prompt(user_input, plan_type)

    max_retries = 3
    base_delay = 2  # Start with 2 seconds

    spinner = LoadingSpinner(f"Crafting your {plan_type} travel plan")
    spinner.start()

    for attempt in range(max_retries):
        try:
            response = model.generate_content(
                contents=prompt,
                generation_config={
                    "temperature": 0.8,         # Slightly creative for engaging content
                    "max_output_tokens": 4096,  # Allow detailed, long itineraries
                },
            )

            spinner.stop()

            if not response.text:
                raise RuntimeError("Vertex AI returned an empty response. Please try again.")

            return response.text

        except Exception as e:
            error_msg = str(e)
            
            # Check for quota/rate limit errors
            is_quota_error = "QUOTA" in error_msg.upper() or "RESOURCE_EXHAUSTED" in error_msg.upper()
            is_credentials_error = "PERMISSION" in error_msg.upper() or "AUTHENTICATION" in error_msg.upper() or "CREDENTIALS" in error_msg.upper()
            
            if is_credentials_error:
                spinner.stop()
                raise RuntimeError(
                    "Authentication failed. Please ensure:\n"
                    "  • GCP_PROJECT_ID is set correctly\n"
                    "  • GOOGLE_APPLICATION_CREDENTIALS points to a valid service account JSON\n"
                    "  • The service account has Vertex AI User role"
                ) from e
            
            if is_quota_error:
                if attempt < max_retries - 1:
                    # Calculate exponential backoff with jitter
                    wait_time = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    spinner.stop()
                    print(f"\n  ⏱️  API quota limit hit. Waiting {wait_time:.1f} seconds before retry ({attempt + 1}/{max_retries})...")
                    time.sleep(wait_time)
                    
                    # Show spinner message for next attempt
                    spinner = LoadingSpinner(f"Crafting your {plan_type} travel plan")
                    spinner.start()
                else:
                    spinner.stop()
                    raise RuntimeError(
                        "Vertex AI quota exceeded after multiple retries.\n\n"
                        "This typically means:\n"
                        "  • Your $5 credits have been exhausted\n"
                        "  • Daily quota limits have been reached\n"
                        "  • Too many requests in a short time\n\n"
                        "Please wait a few minutes and try again, or check your quota at:\n"
                        "  https://console.cloud.google.com/iam-admin/quotas"
                    ) from e
            else:
                spinner.stop()
                raise RuntimeError(f"Failed to generate travel plan: {error_msg}") from e


def generate_both_plans(user_input: UserInput) -> dict:
    """
    Generate both Budget and Premium travel plans sequentially with rate limiting.

    This function is the primary integration point for future frontend use —
    it accepts a UserInput object and returns a plain dict, making it
    straightforward to call from an API route or server-side handler.

    Args:
        user_input: The user's travel preferences.

    Returns:
        Dict with keys "Budget" and "Premium", each containing a plan string.
    """
    plans = {}
    for i, plan_type in enumerate(["Budget", "Premium"]):
        plans[plan_type] = generate_travel_plan(user_input, plan_type)
        
        # Add a small delay between requests to respect API rate limits
        # (not needed after the last request)
        if i < 1:
            time.sleep(1.5)
    
    return plans
