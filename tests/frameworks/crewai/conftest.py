"""Test configuration for CrewAI framework tests."""

import pytest
from agentstack.frameworks.crewai import CrewAIFramework


@pytest.fixture
def crewai_framework():
    """Fixture providing a CrewAIFramework instance for testing."""
    return CrewAIFramework()
