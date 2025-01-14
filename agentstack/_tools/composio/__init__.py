"""Framework-agnostic implementation of composio tools."""

import os
from typing import Any, Dict, List, Optional

from composio import Action, ComposioToolSet
from composio.constants import DEFAULT_ENTITY_ID


def _check_connected_account(app: str, toolset: ComposioToolSet) -> None:
    """Check if connected account exists for the app."""
    connections = toolset.client.connected_accounts.get()
    if app not in [connection.appUniqueId for connection in connections]:
        raise RuntimeError(
            f"No connected account found for app `{app}`; " f"Run `composio add {app}` to fix this"
        )


def execute_action(
    action_name: str,
    params: Dict[str, Any],
    entity_id: Optional[str] = None,
    no_auth: bool = False,
) -> Dict[str, Any]:
    """
    Execute a composio action with given parameters.

    Args:
        action_name: Name of the action to execute
        params: Parameters for the action
        entity_id: Optional entity ID (defaults to DEFAULT_ENTITY_ID)
        no_auth: Whether the action requires authentication

    Returns:
        Dict containing the action result
    """
    toolset = ComposioToolSet()
    action = Action(action_name)

    if not no_auth:
        _check_connected_account(action.app, toolset)

    return toolset.execute_action(
        action=action,
        params=params,
        entity_id=entity_id or DEFAULT_ENTITY_ID,
    )


def get_action_schema(action_name: str) -> Dict[str, Any]:
    """Get the schema for a composio action."""
    toolset = ComposioToolSet()
    action = Action(action_name)
    (action_schema,) = toolset.get_action_schemas(actions=[action])
    return action_schema.model_dump(exclude_none=True)


def find_actions_by_use_case(
    *apps: str,
    use_case: str,
) -> List[Dict[str, Any]]:
    """Find actions by use case."""
    toolset = ComposioToolSet()
    actions = toolset.find_actions_by_use_case(*apps, use_case=use_case)
    return [get_action_schema(action.name) for action in actions]


def find_actions_by_tags(
    *apps: str,
    tags: List[str],
) -> List[Dict[str, Any]]:
    """Find actions by tags."""
    toolset = ComposioToolSet()
    actions = toolset.find_actions_by_tags(*apps, tags=tags)
    return [get_action_schema(action.name) for action in actions]
