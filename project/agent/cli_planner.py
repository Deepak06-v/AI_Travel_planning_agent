"""
CLI travel planner loop: collect preferences, confirm, generate, display.

Separated from ``main.py`` so the repository root stays a thin entrypoint and
this module can later be wrapped by FastAPI, Streamlit, or a proper agent runner
without duplicating prompts.
"""

import sys
from typing import Optional

from project.agent.travel_agent import TravelAgent
from project.config import APP_NAME, BUDGET_TYPES, FOOD_TYPE_OPTIONS, INTEREST_OPTIONS
from project.memory.user_memory import UserMemoryState
from project.models.user_input import UserInput
from project.utils.formatter import (
    Colors,
    print_banner,
    print_error,
    print_info,
    print_itinerary,
    print_plan_header,
    print_preferences_summary,
    print_section_header,
    print_separator,
    print_success,
)


def prompt_input(label: str, required: bool = True) -> str:
    """Prompt the user for a non-empty string input."""
    while True:
        value = input(f"  {Colors.CYAN}▸{Colors.RESET}  {label}: ").strip()
        if value:
            return value
        if not required:
            return ""
        print_error("This field cannot be empty. Please try again.")


def prompt_integer(label: str, min_val: int = 1, max_val: int = 90) -> int:
    """Prompt the user for an integer within a valid range."""
    while True:
        raw = input(f"  {Colors.CYAN}▸{Colors.RESET}  {label} ({min_val}–{max_val}): ").strip()
        try:
            value = int(raw)
            if min_val <= value <= max_val:
                return value
            print_error(f"Please enter a number between {min_val} and {max_val}.")
        except ValueError:
            print_error("Please enter a valid whole number.")


def prompt_choice(label: str, options: list) -> str:
    """Prompt the user to choose one option from a numbered list."""
    print(f"\n  {Colors.CYAN}▸{Colors.RESET}  {label}:")
    for i, option in enumerate(options, 1):
        print(f"      {Colors.DIM}{i}.{Colors.RESET}  {option.capitalize()}")
    while True:
        raw = input(f"  {Colors.CYAN}▸{Colors.RESET}  Enter number (1–{len(options)}): ").strip()
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(options):
                return options[idx]
            print_error(f"Please enter a number between 1 and {len(options)}.")
        except ValueError:
            print_error("Please enter a valid number.")


def prompt_multi_choice(label: str, options: list) -> list:
    """
    Prompt the user to select multiple options by number.
    Entering nothing selects all options.
    """
    print(f"\n  {Colors.CYAN}▸{Colors.RESET}  {label}:")
    for i, option in enumerate(options, 1):
        print(f"      {Colors.DIM}{i}.{Colors.RESET}  {option.capitalize()}")
    print(f"  {Colors.DIM}     (enter numbers separated by commas, or press Enter for all){Colors.RESET}")

    while True:
        raw = input(f"  {Colors.CYAN}▸{Colors.RESET}  Your choices: ").strip()

        if not raw:
            return options[:]

        parts = [p.strip() for p in raw.split(",")]
        selected = []
        valid = True
        for part in parts:
            try:
                idx = int(part) - 1
                if 0 <= idx < len(options):
                    if options[idx] not in selected:
                        selected.append(options[idx])
                else:
                    print_error(f"'{part}' is out of range. Use numbers 1–{len(options)}.")
                    valid = False
                    break
            except ValueError:
                print_error(f"'{part}' is not a valid number.")
                valid = False
                break

        if valid and selected:
            return selected
        elif valid and not selected:
            print_error("Please select at least one interest.")


def collect_user_preferences(memory: Optional[UserMemoryState] = None) -> UserInput:
    """
    Collect travel preferences from the user via CLI.

    Returns a pure ``UserInput`` object for use by services or APIs.
    """
    print_section_header("Tell Us About Your Trip")

    if memory and (
        memory.preferred_budget or memory.travel_interests or memory.preferred_food_type
    ):
        print_info(
            "Loaded saved preferences — you can pick new values below.\n"
            f"    • Budget: {memory.preferred_budget or 'n/a'}\n"
            f"    • Interests: {', '.join(memory.travel_interests) or 'n/a'}\n"
            f"    • Food focus: {memory.preferred_food_type or 'n/a'}\n"
        )

    destination = prompt_input("Where would you like to travel?")
    travel_days = prompt_integer("How many days is your trip?", min_val=1, max_val=30)
    budget_type = prompt_choice("What is your budget style?", BUDGET_TYPES)
    interests = prompt_multi_choice("What are your travel interests?", INTEREST_OPTIONS)
    food_choice = prompt_choice("Preferred food focus", FOOD_TYPE_OPTIONS)
    preferred_food = None if food_choice == "any" else food_choice

    return UserInput(
        destination=destination,
        travel_days=travel_days,
        budget_type=budget_type,
        interests=interests,
        preferred_food_type=preferred_food,
    )


def display_plans(plans: dict, user_input: UserInput):
    """Display generated travel plans in the terminal."""
    for i, (plan_type, content) in enumerate(plans.items(), 1):
        print_plan_header(plan_type, i)
        print_itinerary(content)
        print_separator("─")


def run_planner():
    """
    Main planner loop: collect → generate → display → regenerate or exit.
    """
    print_banner()
    agent = TravelAgent()
    memory_snapshot = agent.memory.load()

    while True:
        try:
            user_input = collect_user_preferences(memory_snapshot)

            print_preferences_summary({
                "Destination": user_input.destination,
                "Travel Days": f"{user_input.travel_days} day(s)",
                "Budget Style": user_input.budget_type.capitalize(),
                "Interests": user_input.interests,
                "Food Focus": user_input.preferred_food_type or "any",
            })

            print()
            confirm = input(
                f"  {Colors.CYAN}▸{Colors.RESET}  Generate plans with these preferences? (Y/n): "
            ).strip().lower()

            if confirm == "n":
                print_info("Starting over...\n")
                memory_snapshot = agent.memory.load()
                continue

            print_section_header("Generating Your Travel Plans")
            print_info("Sit tight — Gemini AI is crafting two personalized itineraries for you.\n")

            plans = agent.generate_both_plans(user_input)

            print_success("Both plans generated successfully!")

            display_plans(plans, user_input)
            agent.persist_session(user_input)
            memory_snapshot = agent.memory.load()

            print_section_header("What Would You Like To Do Next?")
            print(f"  {Colors.DIM}1.{Colors.RESET}  Plan a new trip")
            print(f"  {Colors.DIM}2.{Colors.RESET}  Regenerate plans for the same destination")
            print(f"  {Colors.DIM}3.{Colors.RESET}  Exit")

            choice = input(f"\n  {Colors.CYAN}▸{Colors.RESET}  Enter choice (1/2/3): ").strip()

            if choice == "1":
                print_info("Starting a new trip plan...\n")
                memory_snapshot = agent.memory.load()
                continue
            elif choice == "2":
                print_info("Regenerating plans...\n")
                plans = agent.generate_both_plans(user_input)
                print_success("Plans regenerated!")
                display_plans(plans, user_input)
                agent.persist_session(user_input)
                memory_snapshot = agent.memory.load()
                break
            else:
                print_success(f"Thank you for using {APP_NAME}! Safe travels! ✈")
                break

        except KeyboardInterrupt:
            print(f"\n\n{Colors.YELLOW}  Trip planning cancelled. Safe travels!{Colors.RESET}\n")
            sys.exit(0)
        except RuntimeError as e:
            print_error(str(e))
            retry = input(
                f"\n  {Colors.CYAN}▸{Colors.RESET}  Try again? (Y/n): "
            ).strip().lower()
            if retry == "n":
                sys.exit(1)
            continue
        except Exception as e:
            print_error(f"Unexpected error: {e}")
            sys.exit(1)
