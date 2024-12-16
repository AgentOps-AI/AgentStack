"""Framework-specific exceptions for CrewAI tools."""

from agentstack.exceptions import ToolError


class CrewAIToolError(ToolError):
    """Base exception for CrewAI tool errors."""
    pass


class PipedreamToolError(CrewAIToolError):
    """Exception raised for Pipedream-specific tool errors."""
    pass
