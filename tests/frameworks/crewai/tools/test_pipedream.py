import pytest
from unittest.mock import patch, MagicMock
from agentstack.templates.crewai.tools.pipedream_tool import (
    PipedreamListAppsTool,
    PipedreamListComponentsTool,
    PipedreamGetPropsTool,
    PipedreamActionTool,
    PipedreamSourceTool,
    PipedreamToolError,
)

@pytest.fixture
def mock_pipedream_client():
    with patch('agentstack.templates.crewai.tools.pipedream_tool.PipedreamClient') as mock:
        client = MagicMock()
        mock.return_value = client
        yield client

class TestPipedreamTools:
    def test_list_apps_success(self, mock_pipedream_client):
        mock_pipedream_client.list_apps.return_value = {
            'data': [{'id': 'app1', 'name': 'Test App'}]
        }
        tool = PipedreamListAppsTool(api_key='test_key')
        result = tool._run('')
        assert 'Test App' in str(result)
        mock_pipedream_client.list_apps.assert_called_once_with('')

    def test_list_apps_error(self, mock_pipedream_client):
        mock_pipedream_client.list_apps.side_effect = Exception('API Error')
        tool = PipedreamListAppsTool(api_key='test_key')
        with pytest.raises(PipedreamToolError):
            tool._run('')

    def test_list_components_success(self, mock_pipedream_client):
        mock_pipedream_client.list_components.return_value = {
            'data': [{'id': 'comp1', 'name': 'Test Component'}]
        }
        tool = PipedreamListComponentsTool(api_key='test_key')
        result = tool._run('app_id')
        assert 'Test Component' in str(result)
        mock_pipedream_client.list_components.assert_called_once_with('app_id')

    def test_list_components_error(self, mock_pipedream_client):
        mock_pipedream_client.list_components.side_effect = Exception('API Error')
        tool = PipedreamListComponentsTool(api_key='test_key')
        with pytest.raises(PipedreamToolError):
            tool._run('app_id')

    def test_get_props_success(self, mock_pipedream_client):
        mock_pipedream_client.get_component_definition.return_value = {
            'data': {'props': [{'key': 'api_key', 'type': 'string'}]}
        }
        tool = PipedreamGetPropsTool(api_key='test_key')
        result = tool._run('component_id')
        assert 'api_key' in str(result)
        mock_pipedream_client.get_component_definition.assert_called_once_with('component_id')

    def test_get_props_error(self, mock_pipedream_client):
        mock_pipedream_client.get_component_definition.side_effect = Exception('API Error')
        tool = PipedreamGetPropsTool(api_key='test_key')
        with pytest.raises(PipedreamToolError):
            tool._run('component_id')

    def test_action_success(self, mock_pipedream_client):
        mock_pipedream_client.run_action.return_value = {'status': 'success'}
        tool = PipedreamActionTool(api_key='test_key')
        result = tool._run('123', {'key': 'value'})
        assert 'success' in str(result)
        mock_pipedream_client.run_action.assert_called_once_with('123', {'key': 'value'})

    def test_action_error(self, mock_pipedream_client):
        mock_pipedream_client.run_action.side_effect = Exception('API Error')
        tool = PipedreamActionTool(api_key='test_key')
        with pytest.raises(PipedreamToolError):
            tool._run('123', {'key': 'value'})

    def test_source_success(self, mock_pipedream_client):
        mock_pipedream_client.deploy_source.return_value = {'id': 'src123'}
        tool = PipedreamSourceTool(api_key='test_key')
        result = tool._run('123', 'https://webhook.url', {'key': 'value'})
        assert 'src123' in str(result)
        mock_pipedream_client.deploy_source.assert_called_once_with('123', 'https://webhook.url', {'key': 'value'})

    def test_source_error(self, mock_pipedream_client):
        mock_pipedream_client.deploy_source.side_effect = Exception('API Error')
        tool = PipedreamSourceTool(api_key='test_key')
        with pytest.raises(PipedreamToolError):
            tool._run('123', 'https://webhook.url', {'key': 'value'})
