"""
Application entry point for the WhatsApp Automation system.
Initializes the database, checks environment configuration,
and launches the interactive Terminal UI.
"""

import sys
from config import config
from database import db
from ui import TerminalUI


def initialize_app() -> None:
    """Performs pre-flight checks and initializes storage schema."""
    try:
        # 1. Initialize Database Schema
        db.initialize_schema()

        # 2. Check for configuration readiness
        try:
            config.validate()
        except ValueError as cfg_err:
            print("\n[WARNING]: Configuration Check Failed!")
            print(f"Details: {cfg_err}")
            print("You can manage recipients and prepare messages, but API sending will fail")
            print("until valid credentials are set in your .env file.\n")
            input("Press [Enter] to acknowledge and proceed...")

    except Exception as err:
        print(f"\n[Fatal Error during initialization]: {err}")
        sys.exit(1)


def main() -> None:
    """Runs the main application orchestration."""
    initialize_app()
    ui = TerminalUI()
    
    try:
        ui.run_main_menu()
    except KeyboardInterrupt:
        print("\n\nApplication interrupted by user. Exiting gracefully.")
        sys.exit(0)


if __name__ == "__main__":
    main()