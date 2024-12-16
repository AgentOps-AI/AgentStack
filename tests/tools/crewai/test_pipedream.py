import pytest
from unittest.mock import patch, MagicMock
from agentstack.templates.crewai.tools.pipedream_tool import (
    PipedreamListAppsTool,
    PipedreamListComponentsTool,
    PipedreamGetPropsTool,
    PipedreamActionTool,
    PipedreamSourceTool,
)
from agentstack.exceptions import PipedreamToolError

@pytest.fixture
def mock_pipedream_client():
    with patch('agentstack.templates.crewai.tools.pipedream_tool.PipedreamClient') as mock:
        client = MagicMock()
        mock.return_value = client
        yield client

class TestPipedreamTools:
    def test_list_apps_success(self, mock_pipedream_client):
        mock_pipedream_client.list_apps.return_value = {
            'apps': [{'id': 'app1', 'name': 'Test App'}]
        }
        tool = PipedreamListAppsTool()
        result = tool._execute('')
        assert 'Test App' in result
        mock_pipedream_client.list_apps.assert_called_once()

    def test_list_apps_error(self, mock_pipedream_client):
        mock_pipedream_client.list_apps.side_effect = Exception('API Error')
        tool = PipedreamListAppsTool()
        with pytest.raises(PipedreamToolError) as exc:
            tool._execute('')
        assert 'Failed to list Pipedream apps' in str(exc.value)

    def test_list_components_success(self, mock_pipedream_client):
        mock_pipedream_client.list_components.return_value = {
            'components': [{'id': 'comp1', 'name': 'Test Component'}]
        }
        tool = PipedreamListComponentsTool()
        result = tool._execute('app_id')
        assert 'Test Component' in result
        mock_pipedream_client.list_components.assert_called_once_with('app_id')

    def test_list_components_error(self, mock_pipedream_client):
        mock_pipedream_client.list_components.side_effect = Exception('API Error')
        tool = PipedreamListComponentsTool()
        with pytest.raises(PipedreamToolError) as exc:
            tool._execute('app_id')
        assert 'Failed to list components' in str(exc.value)

    def test_get_props_success(self, mock_pipedream_client):
        mock_pipedream_client.get_component_props.return_value = {
            'props': [{'key': 'api_key', 'type': 'string'}]
        }
        tool = PipedreamGetPropsTool()
        result = tool._execute('component_id')
        assert 'api_key' in result
        mock_pipedream_client.get_component_props.assert_called_once_with('component_id')

    def test_get_props_error(self, mock_pipedream_client):
        mock_pipedream_client.get_component_props.side_effect = Exception('API Error')
        tool = PipedreamGetPropsTool()
        with pytest.raises(PipedreamToolError) as exc:
            tool._execute('component_id')
        assert 'Failed to get component props' in str(exc.value)

    def test_action_success(self, mock_pipedream_client):
        mock_pipedream_client.execute_action.return_value = {'status': 'success'}
        tool = PipedreamActionTool()
        result = tool._execute('{"component_id": "123", "props": {"key": "value"}}')
        assert 'success' in result
        mock_pipedream_client.execute_action.assert_called_once_with('123', {'key': 'value'})

    def test_action_error(self, mock_pipedream_client):
        mock_pipedream_client.execute_action.side_effect = Exception('API Error')
        tool = PipedreamActionTool()
        with pytest.raises(PipedreamToolError) as exc:
            tool._execute('{"component_id": "123", "props": {"key": "value"}}')
        assert 'Failed to execute action' in str(exc.value)

    def test_source_success(self, mock_pipedream_client):
        mock_pipedream_client.deploy_source.return_value = {'id': 'src123'}
        tool = PipedreamSourceTool()
        result = tool._execute('{"component_id": "123", "props": {"key": "value"}}')
        assert 'src123' in result
        mock_pipedream_client.deploy_source.assert_called_once_with('123', {'key': 'value'})

    def test_source_error(self, mock_pipedream_client):
        mock_pipedream_client.deploy_source.side_effect = Exception('API Error')
        tool = PipedreamSourceTool()
        with pytest.raises(PipedreamToolError) as exc:
            tool._execute('{"component_id": "123", "props": {"key": "value"}}')
        assert 'Failed to deploy source' in str(exc.value)

    def test_invalid_json_input(self):
        tool = PipedreamActionTool()
        with pytest.raises(PipedreamToolError) as exc:
            tool._execute('invalid json')
        assert 'Invalid JSON input' in str(exc.value)
