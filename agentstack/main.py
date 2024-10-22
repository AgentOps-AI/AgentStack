import argparse
import sys

from agentstack.cli import init_project_builder, list_tools
from agentstack.utils import get_version
import agentstack.generation as generation


def main():
    parser = argparse.ArgumentParser(
        description="AgentStack CLI - The easiest way to build an agent application"
    )

    parser.add_argument('-v', '--version', action='store_true', help="Show the version")

    # Create top-level subparsers
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # 'init' command
    init_parser = subparsers.add_parser('init', aliases=['i'], help='Initialize a directory for the project')
    init_parser.add_argument('slug_name', nargs='?', help="The directory name to place the project in")
    init_parser.add_argument('--no-wizard', action='store_true', help="Skip wizard steps")

    # 'generate' command
    generate_parser = subparsers.add_parser('generate', aliases=['g'], help='Generate agents or tasks')

    # Subparsers under 'generate'
    generate_subparsers = generate_parser.add_subparsers(dest='generate_command', help='Generate agents or tasks')

    # 'agent' command under 'generate'
    agent_parser = generate_subparsers.add_parser('agent', aliases=['a'], help='Generate an agent')
    agent_parser.add_argument('name', help='Name of the agent')
    agent_parser.add_argument('--role', '-r', help='Role of the agent')
    agent_parser.add_argument('--goal', '-g', help='Goal of the agent')
    agent_parser.add_argument('--backstory', '-b', help='Backstory of the agent')
    agent_parser.add_argument('--llm', '-l', help='Language model to use')

    # 'task' command under 'generate'
    task_parser = generate_subparsers.add_parser('task', aliases=['t'], help='Generate a task')
    task_parser.add_argument('name', help='Name of the task')
    task_parser.add_argument('--description', '-d', help='Description of the task')
    task_parser.add_argument('--expected_output', '-e', help='Expected output of the task')
    task_parser.add_argument('--agent', '-a', help='Agent associated with the task')

    # 'tools' command
    tools_parser = subparsers.add_parser('tools', aliases=['t'], help='Manage tools')

    # Subparsers under 'tools'
    tools_subparsers = tools_parser.add_subparsers(dest='tools_command', help='Tools commands')

    # 'list' command under 'tools'
    tools_list_parser = tools_subparsers.add_parser('list', aliases=['l'], help='List tools')

    # 'add' command under 'tools'
    tools_add_parser = tools_subparsers.add_parser('add', aliases=['a'], help='Add a new tool')
    tools_add_parser.add_argument('name', help='Name of the tool to add')

    # Parse arguments
    args = parser.parse_args()

    # Handle version
    if args.version:
        print(f"AgentStack CLI version: {get_version()}")
        return

    # Handle commands
    if args.command in ['init', 'i']:
        init_project_builder(args.slug_name, args.no_wizard)
    elif args.command in ['generate', 'g']:
        if args.generate_command in ['agent', 'a']:
            generation.generate_agent(args.name, args.role, args.goal, args.backstory, args.llm)
        elif args.generate_command in ['task', 't']:
            generation.generate_task(args.name, args.description, args.expected_output, args.agent)
        else:
            generate_parser.print_help()
    elif args.command in ['tools', 't']:
        if args.tools_command in ['list', 'l']:
            list_tools()
        elif args.tools_command in ['add', 'a']:
            generation.add_tool(args.name)
        else:
            tools_parser.print_help()
    else:
        parser.print_help()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        # Handle Ctrl+C (KeyboardInterrupt)
        print("\nTerminating AgentStack CLI")
        sys.exit(1)
