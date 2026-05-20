"""
Vertex AI Gemini client: authentication, model handle, and text completion.

This module is intentionally free of travel-domain logic — it only turns a
prompt string into model text so other services (itinerary, replanning) can
reuse the same integration point.
"""

import logging
import random
import sys
import threading
import time

import vertexai
from vertexai.generative_models import GenerativeModel

from project.config import GCP_LOCATION, GCP_PROJECT_ID, GEMINI_MODEL

logger = logging.getLogger(__name__)

_vertex_initialized = False


def ensure_vertex_initialized() -> None:
    """Initialize Vertex AI once per process."""
    global _vertex_initialized
    if _vertex_initialized:
        return
    if not GCP_PROJECT_ID:
        raise ValueError(
            "GCP_PROJECT_ID environment variable is not set. "
            "Please set it before running the application."
        )
    vertexai.init(project=GCP_PROJECT_ID, location=GCP_LOCATION)
    _vertex_initialized = True


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


def generate_text_completion(
    prompt: str,
    *,
    spinner_message: str = "Generating",
    temperature: float = 0.8,
    max_output_tokens: int = 4096,
) -> str:
    """
    Run a single Gemini completion for an arbitrary text prompt.

    Args:
        prompt: Full prompt text.
        spinner_message: Short label shown next to the terminal spinner.
        temperature: Model creativity (passed through to Vertex).
        max_output_tokens: Upper bound on response length.

    Returns:
        Model output text.

    Raises:
        ValueError: If GCP project is not configured.
        RuntimeError: On empty response, auth failures, or exhausted retries.
    """
    ensure_vertex_initialized()
    model = GenerativeModel(model_name=GEMINI_MODEL)

    max_retries = 3
    base_delay = 2.0

    spinner = LoadingSpinner(spinner_message)
    spinner.start()

    for attempt in range(max_retries):
        try:
            response = model.generate_content(
                contents=prompt,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": max_output_tokens,
                },
            )

            spinner.stop()

            if not response.text:
                raise RuntimeError("Vertex AI returned an empty response. Please try again.")

            return response.text

        except Exception as e:
            error_msg = str(e)

            is_quota_error = "QUOTA" in error_msg.upper() or "RESOURCE_EXHAUSTED" in error_msg.upper()
            is_credentials_error = (
                "PERMISSION" in error_msg.upper()
                or "AUTHENTICATION" in error_msg.upper()
                or "CREDENTIALS" in error_msg.upper()
            )

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
                    wait_time = base_delay * (2**attempt) + random.uniform(0, 1)
                    spinner.stop()
                    print(
                        f"\n  ⏱️  API quota limit hit. Waiting {wait_time:.1f} seconds "
                        f"before retry ({attempt + 1}/{max_retries})..."
                    )
                    time.sleep(wait_time)
                    spinner = LoadingSpinner(spinner_message)
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

            spinner.stop()
            logger.error("Gemini generate_content failed: %s", error_msg)
            raise RuntimeError(f"Failed to generate travel plan: {error_msg}") from e
