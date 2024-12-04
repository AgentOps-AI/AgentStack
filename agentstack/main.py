import argparse
import os
import sys

from agentstack.cli import init_project_builder, list_tools, configure_default_model
from agentstack.telemetry import track_cli_command
from agentstack.utils import get_version, get_framework
import agentstack.generation as generation
from agentstack.update import check_for_updates

import webbrowser

def main():
    parser = argparse.ArgumentParser(
        description="AgentStack CLI - The easiest way to build an agent application"
    )

    parser.add_argument('-v', '--version', action='store_true', help="Show the version")

    # Create top-level subparsers
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # 'docs' command
    subparsers.add_parser('docs', help='Open Agentstack docs')

    # 'quickstart' command
    subparsers.add_parser('quickstart', help='Open the quickstart guide')

    # 'templates' command
    subparsers.add_parser('templates', help='View Agentstack templates')

    # 'init' command
    init_parser = subparsers.add_parser('init', aliases=['i'], help='Initialize a directory for the project')
    init_parser.add_argument('slug_name', nargs='?', help="The directory name to place the project in")
    init_parser.add_argument('--wizard', '-w', action='store_true', help="Use the setup wizard")
    init_parser.add_argument('--template', '-t', help="Agent template to use")

    # 'run' command
    run_parser = subparsers.add_parser('run', aliases=['r'], help='Run your agent')

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
    tools_add_parser.add_argument('--agents', '-a', help='Name of agents to add this tool to, comma separated')
    tools_add_parser.add_argument('--agent', help='Name of agent to add this tool to')

    # 'remove' command under 'tools'
    tools_remove_parser = tools_subparsers.add_parser('remove', aliases=['r'], help='Remove a tool')
    tools_remove_parser.add_argument('name', help='Name of the tool to remove')

    update = subparsers.add_parser('update', aliases=['u'], help='Check for updates')

    # Parse arguments
    args = parser.parse_args()

    # Handle version
    if args.version:
        print(f"AgentStack CLI version: {get_version()}")
        return

    track_cli_command(args.command)
    check_for_updates(update_requested=args.command in ('update', 'u'))

    # Handle commands
    if args.command in ['docs']:
        webbrowser.open('https://docs.agentstack.sh/')
    elif args.command in ['quickstart']:
        webbrowser.open('https://docs.agentstack.sh/quickstart')
    elif args.command in ['templates']:
        webbrowser.open('https://docs.agentstack.sh/quickstart')
    elif args.command in ['init', 'i']:
        init_project_builder(args.slug_name, args.template, args.wizard)
    elif args.command in ['run', 'r']:
        framework = get_framework()
        if framework == "crewai":
            os.system('python src/main.py')
    elif args.command in ['generate', 'g']:
        if args.generate_command in ['agent', 'a']:
            if not args.llm:
                configure_default_model()
            generation.generate_agent(args.name, args.role, args.goal, args.backstory, args.llm)
        elif args.generate_command in ['task', 't']:
            generation.generate_task(args.name, args.description, args.expected_output, args.agent)
        else:
            generate_parser.print_help()
    elif args.command in ['tools', 't']:
        if args.tools_command in ['list', 'l']:
            list_tools()
        elif args.tools_command in ['add', 'a']:
            agents = [args.agent] if args.agent else None
            agents = args.agents.split(',') if args.agents else agents
            generation.add_tool(args.name, agents=agents)
        elif args.tools_command in ['remove', 'r']:
            generation.remove_tool(args.name)
        else:
            tools_parser.print_help()
    elif args.command in ['update', 'u']:
        pass # Update check already done
    else:
        parser.print_help()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        # Handle Ctrl+C (KeyboardInterrupt)
        print("\nTerminating AgentStack CLI")
        sys.exit(1)
