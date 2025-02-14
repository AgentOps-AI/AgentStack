import sys
import argparse
import webbrowser

from agentstack import conf, log
from agentstack import auth
from agentstack.cli import (
    init_project,
    list_tools,
    add_tool,
    remove_tool,
    add_agent,
    add_task,
    run_project,
    export_template,
    undo,
    export_template,
    create_tool,
)
from agentstack.telemetry import track_cli_command, update_telemetry
from agentstack.utils import get_version, term_color
from agentstack import generation
from agentstack import repo
from agentstack.update import check_for_updates


def _main():
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
    global_parser.add_argument(
        "--no-git",
        help="Disable automatic git commits of changes to your project.",
        dest="no_git",
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
    init_parser.add_argument("--framework", "-f", help="Framework to use")

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
    agent_parser.add_argument("--position", help="Position to add the agent in the stack.")

    # 'task' command under 'generate'
    task_parser = generate_subparsers.add_parser(
        "task", aliases=["t"], help="Generate a task", parents=[global_parser]
    )
    task_parser.add_argument("name", help="Name of the task")
    task_parser.add_argument("--description", "-d", help="Description of the task")
    task_parser.add_argument("--expected_output", "-e", help="Expected output of the task")
    task_parser.add_argument("--agent", "-a", help="Agent associated with the task")
    task_parser.add_argument("--position", help="Position to add the task in the stack.")

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

    # 'new' command under 'tools'
    tools_new_parser = tools_subparsers.add_parser(
        "new", aliases=["n"], help="Create a new custom tool", parents=[global_parser]
    )
    tools_new_parser.add_argument("name", help="Name of the tool to create")
    tools_new_parser.add_argument("--agents", help="Name of agents to add this tool to, comma separated")
    tools_new_parser.add_argument("--agent", help="Name of agent to add this tool to")

    # 'remove' command under 'tools'
    tools_remove_parser = tools_subparsers.add_parser(
        "remove", aliases=["r"], help="Remove a tool", parents=[global_parser]
    )
    tools_remove_parser.add_argument("name", help="Name of the tool to remove")

    export_parser = subparsers.add_parser(
        'export', aliases=['e'], help='Export your agent as a template', parents=[global_parser]
    )
    export_parser.add_argument('filename', help='The name of the file to export to')

    undo_parser = subparsers.add_parser('undo', help='Undo the last change to your project', parents=[global_parser])
    update_parser = subparsers.add_parser('update', aliases=['u'], help='Check for updates', parents=[global_parser])

    # Parse known args and store unknown args in extras; some commands use them later on
    args, extra_args = parser.parse_known_args()

    # Set the project path from --path if it is provided in the global_parser
    conf.set_path(args.project_path)
    # Set the debug flag
    conf.set_debug(args.debug)

    # --no-git flag disables automatic git commits
    if args.no_git:
        repo.dont_track_changes()

    # Handle version
    if args.version:
        log.info(f"AgentStack CLI version: {get_version()}")
        return

    telemetry_id = track_cli_command(args.command, " ".join(sys.argv[1:]))
    check_for_updates(update_requested=args.command in ('update', 'u'))

    # Handle commands
    try:
        # outside of project
        if args.command in ["docs"]:
            webbrowser.open("https://docs.agentstack.sh/")
        elif args.command in ["quickstart"]:
            webbrowser.open("https://docs.agentstack.sh/quickstart")
        elif args.command in ["templates"]:
            webbrowser.open("https://docs.agentstack.sh/templates")
        elif args.command in ["init", "i"]:
            init_project(args.slug_name, args.template, args.framework, args.wizard)
        elif args.command in ["tools", "t"]:
            if args.tools_command in ["list", "l"]:
                list_tools()
            elif args.tools_command in ["add", "a"]:
                agents = [args.agent] if args.agent else None
                agents = args.agents.split(",") if args.agents else agents
                add_tool(args.name, agents)
            elif args.tools_command in ["new", "n"]:
                agents = [args.agent] if args.agent else None
                agents = args.agents.split(",") if args.agents else agents
                create_tool(args.name, agents)
            elif args.tools_command in ["remove", "r"]:
                remove_tool(args.name)
            else:
                tools_parser.print_help()
        elif args.command in ['login']:
            auth.login()
        elif args.command in ['update', 'u']:
            pass  # Update check already done

        # inside project dir commands only
        elif args.command in ["run", "r"]:
            run_project(command=args.function, cli_args=extra_args)
        elif args.command in ['generate', 'g']:
            if args.generate_command in ['agent', 'a']:
                add_agent(
                    name=args.name,
                    role=args.role,
                    goal=args.goal,
                    backstory=args.backstory,
                    llm=args.llm,
                    position=args.position,
                )
            elif args.generate_command in ['task', 't']:
                add_task(
                    name=args.name,
                    description=args.description,
                    expected_output=args.expected_output,
                    agent=args.agent,
                    position=args.position,
                )
            else:
                generate_parser.print_help()
        elif args.command in ['export', 'e']:
            export_template(args.filename)
        elif args.command in ['undo']:
            undo()
        else:
            parser.print_help()

    except Exception as e:
        update_telemetry(telemetry_id, result=1, message=str(e))
        raise e

    update_telemetry(telemetry_id, result=0)


def main() -> int:
    """
    Main entry point for the AgentStack CLI.
    """
    # display logging messages in the console
    log.set_stdout(sys.stdout)
    log.set_stderr(sys.stderr)

    try:
        _main()
        return 0
    except Exception as e:
        log.error(f"An error occurred: \n{e}")
        if not conf.DEBUG:
            log.info("Run again with --debug for more information.")
        log.debug("Full traceback:", exc_info=e)
        return 1
    except KeyboardInterrupt:
        # Handle Ctrl+C (KeyboardInterrupt)
        print("\nTerminating AgentStack CLI")
        return 1


if __name__ == "__main__":
    # Note that since we primarily interact with the CLI through a bin, all logic
    # needs to reside within the main() function.
    # Module syntax is typically only used by tests.
    # see `project.scripts.agentstack` in pyproject.toml for the bin config.
    sys.exit(main())
