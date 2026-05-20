import textwrap


# Terminal color codes
class Colors:
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"


def print_banner():
    """Print a stylized application banner."""
    banner = f"""
{Colors.CYAN}{Colors.BOLD}
╔══════════════════════════════════════════════════════════╗
║          ✈  AI TRAVEL PLANNER AGENT  ✈                  ║
║          Powered by Google Gemini AI                     ║
╚══════════════════════════════════════════════════════════╝
{Colors.RESET}"""
    print(banner)


def print_separator(char: str = "─", width: int = 62, color: str = Colors.DIM):
    """Print a horizontal separator line."""
    print(f"{color}{char * width}{Colors.RESET}")


def print_section_header(title: str):
    """Print a styled section header."""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'━' * 62}{Colors.RESET}")
    print(f"{Colors.BLUE}{Colors.BOLD}  {title.upper()}{Colors.RESET}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'━' * 62}{Colors.RESET}")


def print_plan_header(plan_type: str, plan_number: int):
    """Print a styled plan header (Budget or Premium)."""
    color = Colors.GREEN if plan_type == "Budget" else Colors.YELLOW
    icon = "💰" if plan_type == "Budget" else "⭐"
    print(f"\n{color}{Colors.BOLD}")
    print(f"╔══════════════════════════════════════════════════════════╗")
    print(f"║  {icon}  PLAN {plan_number}: {plan_type.upper()} TRAVEL PLAN{' ' * (44 - len(plan_type))}║")
    print(f"╚══════════════════════════════════════════════════════════╝{Colors.RESET}")


def print_preferences_summary(preferences: dict):
    """Print a formatted summary of user travel preferences."""
    print_section_header("Your Travel Preferences")
    for key, value in preferences.items():
        label = key.replace("_", " ").title()
        if isinstance(value, list):
            value_str = ", ".join(value) if value else "None selected"
        else:
            value_str = str(value)
        print(f"  {Colors.CYAN}▸ {label}:{Colors.RESET} {value_str}")


def print_itinerary(content: str):
    """
    Print the itinerary content with light formatting.
    Wraps long lines for terminal readability.
    """
    terminal_width = 80
    lines = content.split("\n")
    for line in lines:
        stripped = line.strip()

        # Style markdown-style headers (##, ###, **)
        if stripped.startswith("## ") or stripped.startswith("### "):
            heading = stripped.lstrip("#").strip()
            print(f"\n{Colors.CYAN}{Colors.BOLD}  {heading}{Colors.RESET}")
            print(f"  {Colors.DIM}{'·' * min(len(heading) + 2, 60)}{Colors.RESET}")

        elif stripped.startswith("**") and stripped.endswith("**"):
            inner = stripped.strip("*").strip()
            print(f"\n{Colors.YELLOW}{Colors.BOLD}  {inner}{Colors.RESET}")

        elif stripped.startswith("- ") or stripped.startswith("* "):
            bullet_text = stripped[2:].strip()
            wrapped = textwrap.fill(bullet_text, width=terminal_width - 6,
                                    subsequent_indent="       ")
            print(f"  {Colors.GREEN}  •{Colors.RESET}  {wrapped}")

        elif stripped.startswith("1.") or (len(stripped) > 2 and stripped[0].isdigit() and stripped[1] == "."):
            print(f"  {Colors.YELLOW}  {stripped}{Colors.RESET}")

        elif stripped == "":
            print()

        else:
            wrapped = textwrap.fill(stripped, width=terminal_width - 4,
                                    subsequent_indent="    ")
            print(f"  {wrapped}")


def print_error(message: str):
    """Print a formatted error message."""
    print(f"\n{Colors.RED}{Colors.BOLD}  ✗ ERROR:{Colors.RESET} {Colors.RED}{message}{Colors.RESET}")


def print_success(message: str):
    """Print a formatted success message."""
    print(f"\n{Colors.GREEN}{Colors.BOLD}  ✓{Colors.RESET} {message}")


def print_info(message: str):
    """Print a formatted info message."""
    print(f"  {Colors.CYAN}ℹ{Colors.RESET}  {message}")
