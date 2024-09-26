import argparse
import sys

from cli import init_project_builder
from utils import get_version


def main():
    parser = argparse.ArgumentParser(
        description="AgentStack CLI - The easiest way to build an agent application"
    )
    parser.add_argument('-v', '--version', action='store_true', help="Show the version")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    init_parser = subparsers.add_parser('init', help='Initialize a directory for the project')

    # Parse arguments
    args = parser.parse_args()

    if args.version:
        print(f"AgentStack CLI version: {get_version()}")
        return

    # Command logic
    if args.command == "init":
        init_project_builder()
    else:
        parser.print_help()


try:
    main()
except KeyboardInterrupt:
    # Handle Ctrl+C (KeyboardInterrupt)
    print("\nTerminating AgentStack CLI")
    sys.exit(1)