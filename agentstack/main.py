import sys
import argparse
import webbrowser

from agentstack import conf, auth
from agentstack.cli import (
    init_project_builder,
    add_tool,
    list_tools,
    configure_default_model,
    run_project,
    export_template,
)
from agentstack.telemetry import track_cli_command, update_telemetry
from agentstack.utils import get_version, term_color
from agentstack import generation
from agentstack.update import check_for_updates


def main():
    global_parser = argparse.ArgumentParser(add_help=False)
    global_parser.add_argument(
        "--path",
        "-p",
        help="Path to the project directory, defaults to current working directory",
        dest="project_path",
    )
    global_parser.add_argument(
        "--debug",
        help="Print more information when an error occurs",
        dest="debug",
        action="store_true",
    )

    parser = argparse.ArgumentParser(
        parents=[global_parser], description="AgentStack CLI - The easiest way to build an agent application"
    )

    parser.add_argument("-v", "--version", action="store_true", help="Show the version")

    # Create top-level subparsers
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # 'docs' command
    subparsers.add_parser("docs", help="Open Agentstack docs")

    # 'quickstart' command
    subparsers.add_parser("quickstart", help="Open the quickstart guide")

    # 'templates' command
    subparsers.add_parser("templates", help="View Agentstack templates")

    # 'login' command
    subparsers.add_parser("login", help="Authenticate with Agentstack.sh")

    # 'init' command
    init_parser = subparsers.add_parser(
        "init", aliases=["i"], help="Initialize a directory for the project", parents=[global_parser]
    )
    init_parser.add_argument("slug_name", nargs="?", help="The directory name to place the project in")
    init_parser.add_argument("--wizard", "-w", action="store_true", help="Use the setup wizard")
    init_parser.add_argument("--template", "-t", help="Agent template to use")

    # 'run' command
    run_parser = subparsers.add_parser(
        "run",
        aliases=["r"],
        help="Run your agent",
        parents=[global_parser],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
  --input-<key>=VALUE   Specify inputs to be passed to the run. 
                        These will override the inputs in the project's inputs.yaml file.
                        Examples: --input-topic=Sports --input-content-type=News
    ''',
    )
    run_parser.add_argument(
        "--function",
        "-f",
        help="Function to call in main.py, defaults to 'run'",
        default="run",
        dest="function",
    )

    # 'generate' command
    generate_parser = subparsers.add_parser(
        "generate", aliases=["g"], help="Generate agents or tasks", parents=[global_parser]
    )

    # Subparsers under 'generate'
    generate_subparsers = generate_parser.add_subparsers(
        dest="generate_command", help="Generate agents or tasks"
    )

    # 'agent' command under 'generate'
    agent_parser = generate_subparsers.add_parser(
        "agent", aliases=["a"], help="Generate an agent", parents=[global_parser]
    )
    agent_parser.add_argument("name", help="Name of the agent")
    agent_parser.add_argument("--role", "-r", help="Role of the agent")
    agent_parser.add_argument("--goal", "-g", help="Goal of the agent")
    agent_parser.add_argument("--backstory", "-b", help="Backstory of the agent")
    agent_parser.add_argument("--llm", "-l", help="Language model to use")

    # 'task' command under 'generate'
    task_parser = generate_subparsers.add_parser(
        "task", aliases=["t"], help="Generate a task", parents=[global_parser]
    )
    task_parser.add_argument("name", help="Name of the task")
    task_parser.add_argument("--description", "-d", help="Description of the task")
    task_parser.add_argument("--expected_output", "-e", help="Expected output of the task")
    task_parser.add_argument("--agent", "-a", help="Agent associated with the task")

    # 'tools' command
    tools_parser = subparsers.add_parser("tools", aliases=["t"], help="Manage tools")

    # Subparsers under 'tools'
    tools_subparsers = tools_parser.add_subparsers(dest="tools_command", help="Tools commands")

    # 'list' command under 'tools'
    _ = tools_subparsers.add_parser("list", aliases=["l"], help="List tools")

    # 'add' command under 'tools'
    tools_add_parser = tools_subparsers.add_parser(
        "add", aliases=["a"], help="Add a new tool", parents=[global_parser]
    )
    tools_add_parser.add_argument("name", help="Name of the tool to add", nargs="?")
    tools_add_parser.add_argument(
        "--agents", "-a", help="Name of agents to add this tool to, comma separated"
    )
    tools_add_parser.add_argument("--agent", help="Name of agent to add this tool to")

    # 'remove' command under 'tools'
    tools_remove_parser = tools_subparsers.add_parser(
        "remove", aliases=["r"], help="Remove a tool", parents=[global_parser]
    )
    tools_remove_parser.add_argument("name", help="Name of the tool to remove")

    export_parser = subparsers.add_parser(
        'export', aliases=['e'], help='Export your agent as a template', parents=[global_parser]
    )
    export_parser.add_argument('filename', help='The name of the file to export to')

    update = subparsers.add_parser('update', aliases=['u'], help='Check for updates', parents=[global_parser])

    # Parse known args and store unknown args in extras; some commands use them later on
    args, extra_args = parser.parse_known_args()

    # Set the project path from --path if it is provided in the global_parser
    conf.set_path(args.project_path)

    # Handle version
    if args.version:
        print(f"AgentStack CLI version: {get_version()}")
        sys.exit(0)

    telemetry_id = track_cli_command(args.command, " ".join(sys.argv[1:]))
    check_for_updates(update_requested=args.command in ('update', 'u'))

    # Handle commands
    try:
        if args.command in ["docs"]:
            webbrowser.open("https://docs.agentstack.sh/")
        elif args.command in ["quickstart"]:
            webbrowser.open("https://docs.agentstack.sh/quickstart")
        elif args.command in ["templates"]:
            webbrowser.open("https://docs.agentstack.sh/quickstart")
        elif args.command in ["init", "i"]:
            init_project_builder(args.slug_name, args.template, args.wizard)
        elif args.command in ["run", "r"]:
            run_project(command=args.function, debug=args.debug, cli_args=extra_args)
        elif args.command in ['generate', 'g']:
            if args.generate_command in ['agent', 'a']:
                if not args.llm:
                    configure_default_model()
                generation.add_agent(args.name, args.role, args.goal, args.backstory, args.llm)
            elif args.generate_command in ['task', 't']:
                generation.add_task(args.name, args.description, args.expected_output, args.agent)
            else:
                generate_parser.print_help()
        elif args.command in ["tools", "t"]:
            if args.tools_command in ["list", "l"]:
                list_tools()
            elif args.tools_command in ["add", "a"]:
                agents = [args.agent] if args.agent else None
                agents = args.agents.split(",") if args.agents else agents
                add_tool(args.name, agents)
            elif args.tools_command in ["remove", "r"]:
                generation.remove_tool(args.name)
            else:
                tools_parser.print_help()
        elif args.command in ['export', 'e']:
            export_template(args.filename)
        elif args.command in ['login']:
            auth.login()
        elif args.command in ['update', 'u']:
            pass  # Update check already done
        else:
            parser.print_help()
    except Exception as e:
        update_telemetry(telemetry_id, result=1, message=str(e))
        print(term_color("An error occurred while running your AgentStack command:", "red"))
        raise e

    update_telemetry(telemetry_id, result=0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # Handle Ctrl+C (KeyboardInterrupt)
        print("\nTerminating AgentStack CLI")
        sys.exit(1)
