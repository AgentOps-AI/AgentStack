import unittest
from unittest.mock import patch, MagicMock, call
import time
import threading
from io import StringIO
from agentstack.cli.spinner import Spinner


class TestSpinner(unittest.TestCase):
    def setUp(self):
        """Set up test cases."""
        self.mock_stdout_patcher = patch('sys.stdout', new_callable=StringIO)
        self.mock_stdout = self.mock_stdout_patcher.start()

        self.mock_terminal_patcher = patch('shutil.get_terminal_size')
        self.mock_terminal = self.mock_terminal_patcher.start()
        self.mock_terminal.return_value = MagicMock(columns=80)

        # Patch the log module where Spinner is importing it
        self.mock_log_patcher = patch('agentstack.cli.spinner.log')
        self.mock_log = self.mock_log_patcher.start()

    def tearDown(self):
        """Clean up after tests."""
        self.mock_stdout_patcher.stop()
        self.mock_terminal_patcher.stop()
        self.mock_log_patcher.stop()

    def test_spinner_initialization(self):
        """Test spinner initialization."""
        spinner = Spinner(message="Test")
        self.assertEqual(spinner.message, "Test")
        self.assertEqual(spinner.delay, 0.1)
        self.assertFalse(spinner.running)
        self.assertIsNone(spinner.spinner_thread)
        self.assertIsNone(spinner.start_time)

    def test_context_manager(self):
        """Test spinner works as context manager."""
        with Spinner("Test") as spinner:
            self.assertTrue(spinner.running)
            self.assertTrue(spinner.spinner_thread.is_alive())
            time.sleep(0.2)

        self.assertFalse(spinner.running)
        self.assertFalse(spinner.spinner_thread.is_alive())

    def test_clear_and_log(self):
        """Test clear_and_log functionality."""
        test_message = "Test log message"
        with Spinner("Test") as spinner:
            spinner.clear_and_log(test_message)
            time.sleep(0.2)

        # Verify log.success was called with the message
        self.mock_log.success.assert_called_once_with(test_message)

    def test_concurrent_logging(self):
        """Test thread safety of logging while spinner is running."""
        messages = ["Message 0", "Message 1", "Message 2"]

        def log_messages(spinner):
            for msg in messages:
                spinner.clear_and_log(msg)
                time.sleep(0.1)

        with Spinner("Test") as spinner:
            thread = threading.Thread(target=log_messages, args=(spinner,))
            thread.start()
            thread.join()

        # Verify all messages were logged
        self.assertEqual(self.mock_log.success.call_count, len(messages))
        self.mock_log.success.assert_has_calls([call(msg) for msg in messages])

    def test_thread_cleanup(self):
        """Test proper thread cleanup after stopping."""
        spinner = Spinner("Test")
        spinner.start()
        time.sleep(0.2)
        spinner.clear_and_log("Test message")
        spinner.stop()

        # Give thread time to clean up
        time.sleep(0.1)
        self.assertFalse(spinner.running)
        self.assertFalse(spinner.spinner_thread.is_alive())
        self.mock_log.success.assert_called_once_with("Test message")

    def test_rapid_message_updates(self):
        """Test spinner handles rapid message updates and logging."""
        messages = [f"Message {i}" for i in range(5)]
        with Spinner("Initial") as spinner:
            for msg in messages:
                spinner.update_message(msg)
                spinner.clear_and_log(f"Logged: {msg}")
                time.sleep(0.05)

        # Verify all messages were logged
        self.assertEqual(self.mock_log.success.call_count, len(messages))
        self.mock_log.success.assert_has_calls([
            call(f"Logged: {msg}") for msg in messages
        ])

    @patch('time.time')
    def test_elapsed_time_display(self, mock_time):
        """Test elapsed time is displayed correctly."""
        mock_time.side_effect = [1000, 1001, 1002]  # Mock timestamps

        with Spinner("Test") as spinner:
            spinner.clear_and_log("Time check")
            time.sleep(0.2)
            output = self.mock_stdout.getvalue()
            self.assertIn("[1.0s]", output)
            self.mock_log.success.assert_called_once_with("Time check")

