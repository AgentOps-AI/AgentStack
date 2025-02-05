"""
AgentStack tool integration for the full Daytona SDK.

This module wraps the Daytona SDK so that AgentStack agents can create AI sandbox,
run OS and Python commands, manage file operations, conduct Git operations,
and even invoke LSP functions.

Exported functions:
  [Workspace Lifecycle]
    - create_workspace(language: str = "python") -> dict
    - stop_workspace(workspace_id: str) -> dict
    - start_workspace(workspace_id: str) -> dict
    - remove_workspace(workspace_id: str) -> dict

  [Process Execution]
    - exec_command(workspace_id: str, command: str, cwd: str = "/home/daytona", timeout: int = 10) -> dict
    - code_run(workspace_id: str, code: str) -> dict

  [Session-based Execution]
    - create_exec_session(workspace_id: str, session_id: str) -> dict
    - get_session(workspace_id: str, session_id: str) -> dict
    - execute_session_command(workspace_id: str, session_id: str, command: str) -> dict
    - get_session_command(workspace_id: str, session_id: str, cmd_id: str) -> dict
    - get_session_command_logs(workspace_id: str, session_id: str, cmd_id: str) -> dict
    - list_sessions(workspace_id: str) -> list
    - delete_session(workspace_id: str, session_id: str) -> dict

  [File Operations]
    - list_files(workspace_id: str, directory: str) -> list
    - create_folder(workspace_id: str, folder: str, mode: str) -> None
    - upload_file(workspace_id: str, file_path: str, file_content: bytes) -> None
    - find_files(workspace_id: str, directory: str, query: str) -> list
    - replace_in_files(workspace_id: str, file_paths: list[str], old: str, new: str) -> None
    - download_file(workspace_id: str, file_path: str) -> bytes
    - set_file_permissions(workspace_id: str, file_path: str, mode: str) -> None
    - get_file_info(workspace_id: str, file_path: str) -> dict
    - move_files(workspace_id: str, src: str, dst: str) -> None
    - delete_file(workspace_id: str, file_path: str) -> None

  [Git Operations]
    - git_clone(workspace_id: str, repo_url: str, target_dir: str, branch: str = "master") -> None
    - git_pull(workspace_id: str, repo_dir: str) -> None

  [Language Server Protocol (LSP) Operations]
    - create_lsp_server(workspace_id: str, language: str, project_dir: str) -> object
    - lsp_did_open(lsp_server: object, file: str) -> None
    - lsp_did_close(lsp_server: object, file: str) -> None
    - lsp_document_symbols(lsp_server: object, file: str) -> list
    - lsp_completions(lsp_server: object, file: str, position: dict) -> list

    You need to add the following lines to your project’s .env file (or set them in your
    deployment environment):
        DAYTONA_SERVER_URL="https://your-daytona-server.com"
        DAYTONA_API_KEY="your_daytona_api_key"
"""

from typing import Any, Dict, List
from daytona_sdk import Daytona, CreateWorkspaceParams, SessionExecuteRequest


# Helper: get a Daytona instance (stateless) and retrieve an existing workspace
def _get_workspace(workspace_id: str) -> Any:
    daytona = Daytona()
    return daytona.get_current_workspace(workspace_id)


# ─────── Workspace Lifecycle ───────


def create_workspace(language: str = "python") -> Dict[str, Any]:
    """
    Create a new workspace.

    Args:
        language: Programming language ("python" or "typescript"). Defaults to "python".
    Returns:
        Dictionary with keys `workspace_id` and `root` (workspace root directory).
    """
    daytona = Daytona()
    params = CreateWorkspaceParams(language=language)
    workspace = daytona.create(params)
    root_dir = workspace.get_workspace_root_dir()
    return {"workspace_id": workspace.id, "root": root_dir}


def stop_workspace(workspace_id: str) -> Dict[str, Any]:
    """
    Stop an existing workspace.

    Args:
        workspace_id: The workspace identifier.
    Returns:
        Dictionary indicating the stopped status.
    """
    ws = _get_workspace(workspace_id)
    Daytona().stop(ws)
    return {"workspace_id": workspace_id, "status": "stopped"}


def start_workspace(workspace_id: str) -> Dict[str, Any]:
    """
    Start a previously stopped workspace.

    Args:
        workspace_id: The workspace identifier.
    Returns:
        Dictionary indicating the running status.
    """
    ws = _get_workspace(workspace_id)
    Daytona().start(ws)
    return {"workspace_id": workspace_id, "status": "started"}


def remove_workspace(workspace_id: str) -> Dict[str, Any]:
    """
    Remove (delete) a workspace.

    Args:
        workspace_id: The workspace identifier.
    Returns:
        Dictionary indicating the removal of the workspace.
    """
    daytona = Daytona()
    ws = _get_workspace(workspace_id)
    daytona.remove(ws)
    return {"workspace_id": workspace_id, "status": "removed"}


# ─────── Process Execution ───────


def exec_command(
    workspace_id: str, command: str, cwd: str = "/home/daytona", timeout: int = 10
) -> Dict[str, Any]:
    """
    Execute a shell command in a workspace.

    Args:
        workspace_id: Workspace identifier.
        command: The command to execute.
        cwd: Working directory for the command.
        timeout: Timeout in seconds.
    Returns:
        Dictionary with `exit_code` and `result` (output or error).
    """
    ws = _get_workspace(workspace_id)
    response = ws.process.exec(command, cwd=cwd, timeout=timeout)
    return {"exit_code": response.exit_code, "result": response.result}


def code_run(workspace_id: str, code: str) -> Dict[str, Any]:
    """
    Run Python code securely inside the workspace.

    Args:
        workspace_id: Workspace identifier.
        code: The code to execute.
    Returns:
        Dictionary with `exit_code` and `result`.
    """
    ws = _get_workspace(workspace_id)
    response = ws.process.code_run(code)
    return {"exit_code": response.exit_code, "result": response.result}


# ─────── Session-based Execution ───────


def create_exec_session(workspace_id: str, session_id: str) -> Dict[str, Any]:
    """
    Create an execution session for running multiple commands.

    Args:
        workspace_id: Workspace identifier.
        session_id: A unique identifier for the session.
    Returns:
        Dictionary confirming session creation.
    """
    ws = _get_workspace(workspace_id)
    ws.process.create_session(session_id)
    return {"workspace_id": workspace_id, "session_id": session_id, "status": "session created"}


def get_session(workspace_id: str, session_id: str) -> Dict[str, Any]:
    """
    Retrieve details about an execution session.

    Args:
        workspace_id: Workspace identifier.
        session_id: The session identifier.
    Returns:
        Dictionary with session details.
    """
    ws = _get_workspace(workspace_id)
    session_info = ws.process.get_session(session_id)
    return {"workspace_id": workspace_id, "session_id": session_id, "session": session_info}


def execute_session_command(workspace_id: str, session_id: str, command: str) -> Dict[str, Any]:
    """
    Execute a command within an already created session.

    Args:
        workspace_id: Workspace identifier.
        session_id: The session identifier.
        command: The command to execute.
    Returns:
        Dictionary with `cmd_id`, `exit_code`, and `output`.
    """
    ws = _get_workspace(workspace_id)
    req = SessionExecuteRequest(command=command)
    resp = ws.process.execute_session_command(session_id, req)
    return {
        "session_id": session_id,
        "cmd_id": resp.cmd_id,
        "exit_code": resp.exit_code,
        "output": resp.output,
    }


def get_session_command(workspace_id: str, session_id: str, cmd_id: str) -> Dict[str, Any]:
    """
    Get details of a particular session command.

    Args:
        workspace_id: Workspace identifier.
        session_id: The session identifier.
        cmd_id: The command id.
    Returns:
        Dictionary with command details.
    """
    ws = _get_workspace(workspace_id)
    cmd_info = ws.process.get_session_command(session_id, cmd_id)
    return {"session_id": session_id, "cmd_id": cmd_id, "command_info": cmd_info}


def get_session_command_logs(workspace_id: str, session_id: str, cmd_id: str) -> Dict[str, Any]:
    """
    Retrieve the logs for a specific session command.

    Args:
        workspace_id: Workspace identifier.
        session_id: The session identifier.
        cmd_id: The command id.
    Returns:
        Dictionary containing the logs.
    """
    ws = _get_workspace(workspace_id)
    logs = ws.process.get_session_command_logs(session_id, cmd_id)
    return {"session_id": session_id, "cmd_id": cmd_id, "logs": logs}


def list_sessions(workspace_id: str) -> List[Any]:
    """
    List all active sessions within the workspace.

    Args:
        workspace_id: Workspace identifier.
    Returns:
        List of session details.
    """
    ws = _get_workspace(workspace_id)
    return ws.process.list_sessions()


def delete_session(workspace_id: str, session_id: str) -> Dict[str, Any]:
    """
    Delete an execution session.

    Args:
        workspace_id: Workspace identifier.
        session_id: The session identifier.
    Returns:
        Dictionary confirming deletion.
    """
    ws = _get_workspace(workspace_id)
    ws.process.delete_session(session_id)
    return {"workspace_id": workspace_id, "session_id": session_id, "status": "session deleted"}


# ─────── File Operations ───────


def list_files(workspace_id: str, directory: str) -> List[str]:
    """
    List all files in the specified directory inside the workspace.

    Args:
        workspace_id: Workspace identifier.
        directory: Directory path inside the workspace.
    Returns:
        List of file paths.
    """
    ws = _get_workspace(workspace_id)
    return ws.fs.list_files(directory)


def create_folder(workspace_id: str, folder: str, mode: str) -> None:
    """
    Create a folder in the workspace file system.

    Args:
        workspace_id: Workspace identifier.
        folder: The folder path to create.
        mode: Permissions mode (e.g. "755").
    """
    ws = _get_workspace(workspace_id)
    ws.fs.create_folder(folder, mode)


def upload_file(workspace_id: str, file_path: str, file_content: bytes) -> None:
    """
    Upload a file to the workspace.

    Args:
        workspace_id: Workspace identifier.
        file_path: Destination path in the workspace.
        file_content: File content as bytes.
    """
    ws = _get_workspace(workspace_id)
    ws.fs.upload_file(file_path, file_content)


def find_files(workspace_id: str, directory: str, query: str) -> List[Any]:
    """
    Search for files in the workspace that contain a given query string.

    Args:
        workspace_id: Workspace identifier.
        directory: Directory to search within.
        query: The text to search for.
    Returns:
        List of matching file details.
    """
    ws = _get_workspace(workspace_id)
    return ws.fs.find_files(directory, query)


def replace_in_files(workspace_id: str, file_paths: List[str], old: str, new: str) -> None:
    """
    Replace occurrences of a string with a new string in specified files.

    Args:
        workspace_id: Workspace identifier.
        file_paths: List of file paths to search.
        old: Original text.
        new: Replacement text.
    """
    ws = _get_workspace(workspace_id)
    ws.fs.replace_in_files(file_paths, old, new)


def download_file(workspace_id: str, file_path: str) -> bytes:
    """
    Download a file from the workspace.

    Args:
        workspace_id: Workspace identifier.
        file_path: The path to the file.
    Returns:
        The file content as bytes.
    """
    ws = _get_workspace(workspace_id)
    return ws.fs.download_file(file_path)


def set_file_permissions(workspace_id: str, file_path: str, mode: str) -> None:
    """
    Change a file's permissions in the workspace.

    Args:
        workspace_id: Workspace identifier.
        file_path: Path to the file.
        mode: New permission mode (e.g. "777").
    """
    ws = _get_workspace(workspace_id)
    ws.fs.set_file_permissions(file_path, mode=mode)


def get_file_info(workspace_id: str, file_path: str) -> Dict[str, Any]:
    """
    Get information about a file in the workspace.

    Args:
        workspace_id: Workspace identifier.
        file_path: Path to the file.
    Returns:
        Dictionary containing file metadata.
    """
    ws = _get_workspace(workspace_id)
    return ws.fs.get_file_info(file_path)


def move_files(workspace_id: str, src: str, dst: str) -> None:
    """
    Move a file from src path to dst path inside the workspace.

    Args:
        workspace_id: Workspace identifier.
        src: Source file path.
        dst: Destination file path.
    """
    ws = _get_workspace(workspace_id)
    ws.fs.move_files(src, dst)


def delete_file(workspace_id: str, file_path: str) -> None:
    """
    Delete a file in the workspace.

    Args:
        workspace_id: Workspace identifier.
        file_path: Path to the file.
    """
    ws = _get_workspace(workspace_id)
    ws.fs.delete_file(file_path)


# ─────── Git Operations ───────


def git_clone(workspace_id: str, repo_url: str, target_dir: str, branch: str = "master") -> None:
    """
    Clone a Git repository into the workspace.

    Args:
        workspace_id: Workspace identifier.
        repo_url: URL of the repository.
        target_dir: Directory in the workspace where the repository will be cloned.
        branch: Branch name to clone. Defaults to "master".
    """
    ws = _get_workspace(workspace_id)
    ws.git.clone(repo_url, target_dir, branch)


def git_pull(workspace_id: str, repo_dir: str) -> None:
    """
    Pull the latest changes in a Git repository in the workspace.

    Args:
        workspace_id: Workspace identifier.
        repo_dir: The directory of the cloned repository.
    """
    ws = _get_workspace(workspace_id)
    ws.git.pull(repo_dir)


# ─────── LSP (Language Server Protocol) Operations ───────


def create_lsp_server(workspace_id: str, language: str, project_dir: str) -> Any:
    """
    Create an LSP server for a project in the workspace.

    Args:
        workspace_id: Workspace identifier.
        language: Language (for example, "typescript").
        project_dir: The project directory in the workspace.
    Returns:
        The LSP server object.
    """
    ws = _get_workspace(workspace_id)
    return ws.create_lsp_server(language, project_dir)


def lsp_did_open(lsp_server: Any, file: str) -> None:
    """
    Notify the LSP server that a document has been opened.

    Args:
        lsp_server: The LSP server object.
        file: The file that was opened.
    """
    lsp_server.did_open(file)


def lsp_did_close(lsp_server: Any, file: str) -> None:
    """
    Notify the LSP server that a document has been closed.

    Args:
        lsp_server: The LSP server object.
        file: The file that was closed.
    """
    lsp_server.did_close(file)


def lsp_document_symbols(lsp_server: Any, file: str) -> List[Any]:
    """
    Get all symbols from a document via the LSP server.

    Args:
        lsp_server: The LSP server object.
        file: The file to analyze.
    Returns:
        A list of document symbols.
    """
    return lsp_server.document_symbols(file)


def lsp_completions(lsp_server: Any, file: str, position: Dict[str, int]) -> List[Any]:
    """
    Get completion suggestions for the file at the given position.

    Args:
        lsp_server: The LSP server object.
        file: The file to analyze.
        position: Dictionary with keys "line" and "character".
    Returns:
        A list of completion suggestions.
    """
    return lsp_server.completions(file, position)
