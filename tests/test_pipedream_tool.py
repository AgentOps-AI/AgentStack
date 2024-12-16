import unittest
from unittest.mock import patch, MagicMock
from agentstack.tools import ToolConfig
from agentstack.templates.crewai.tools.pipedream_tool import PipedreamActionTool, PipedreamTriggerTool


class TestPipedreamTool(unittest.TestCase):
    def test_pipedream_config(self):
        """Test that the Pipedream tool configuration is valid."""
        tool_conf = ToolConfig.from_tool_name('pipedream')
        self.assertEqual(tool_conf.name, 'pipedream')
        self.assertEqual(tool_conf.category, 'api')
        self.assertIn('pipedream_action', tool_conf.tools)
        self.assertIn('pipedream_trigger', tool_conf.tools)

    @patch('requests.post')
    def test_pipedream_action(self, mock_post):
        """Test that the Pipedream action tool executes components correctly."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "success"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        # Create tool and execute
        tool = PipedreamActionTool()
        result = tool._run('test_component_id', {'param': 'value'})

        # Verify
        self.assertEqual(result, '{\n  "status": "success"\n}')
        mock_post.assert_called_once_with(
            'https://api.pipedream.com/v1/components/test_component_id/event',
            headers={'Authorization': 'Bearer None', 'Content-Type': 'application/json'},
            json={'param': 'value'},
        )

    @patch('requests.post')
    def test_pipedream_action_error(self, mock_post):
        """Test that the Pipedream action tool handles errors correctly."""
        # Setup mock error
        mock_post.side_effect = Exception('API Error')

        # Create tool and execute
        tool = PipedreamActionTool()
        result = tool._run('test_component_id')

        # Verify
        self.assertEqual(result, 'Error executing Pipedream component: API Error')
        mock_post.assert_called_once()

    @patch('requests.get')
    def test_pipedream_trigger(self, mock_get):
        """Test that the Pipedream trigger tool lists events correctly."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.json.return_value = [{"event": "test"}]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Create tool and execute
        tool = PipedreamTriggerTool()
        result = tool._run('test_component_id')

        # Verify
        self.assertEqual(result, '[\n  {\n    "event": "test"\n  }\n]')
        mock_get.assert_called_once_with(
            'https://api.pipedream.com/v1/components/test_component_id/events',
            headers={'Authorization': 'Bearer None', 'Content-Type': 'application/json'},
        )

    @patch('requests.get')
    def test_pipedream_trigger_error(self, mock_get):
        """Test that the Pipedream trigger tool handles errors correctly."""
        # Setup mock error
        mock_get.side_effect = Exception('API Error')

        # Create tool and execute
        tool = PipedreamTriggerTool()
        result = tool._run('test_component_id')

        # Verify
        self.assertEqual(result, 'Error listing Pipedream events: API Error')
        mock_get.assert_called_once()


if __name__ == '__main__':
    unittest.main()
