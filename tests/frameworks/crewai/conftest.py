"""Test configuration for CrewAI framework tests."""

import pytest
from agentstack.frameworks.crewai import CrewAIFramework
from agentstack.templates.crewai.tools.pipedream_tool import PipedreamClient


@pytest.fixture
def crewai_framework():
    """Fixture providing a CrewAIFramework instance for testing."""
    return CrewAIFramework()


@pytest.fixture
def api_key():
    return "test_key"


@pytest.fixture
def pipedream_client(api_key):
    return PipedreamClient(api_key)
