"""
AI Travel Planner — CLI entry point (thin wrapper).

All behavior lives under the ``project`` package; this file only ensures the
repository root is on ``sys.path`` and starts the CLI planner loop.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from project.logging_config import setup_logging

setup_logging()

from project.agent.cli_planner import run_planner


if __name__ == "__main__":
    run_planner()
