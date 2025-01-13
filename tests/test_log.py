import unittest
import sys
import io
import logging
import shutil
from pathlib import Path
from agentstack import log, conf
from agentstack.log import SUCCESS, NOTIFY

BASE_PATH = Path(__file__).parent


class TestLog(unittest.TestCase):
    def setUp(self):
        # Create test directory if it doesn't exist
        self.test_dir = BASE_PATH / 'tmp/test_log'
        self.test_dir.mkdir(parents=True, exist_ok=True)

        # Set log file to test directory
        self.test_log_file = self.test_dir / 'test.log'
        log.LOG_FILENAME = self.test_log_file

        # Create string IO objects to capture stdout/stderr
        self.stdout = io.StringIO()
        self.stderr = io.StringIO()

        # Set up clean logging instance
        log.instance = None
        log.set_stdout(self.stdout)
        log.set_stderr(self.stderr)

    def tearDown(self):
        # Clean up test directory
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

        # Clear string IO buffers
        self.stdout.close()
        self.stderr.close()

    def test_debug_message(self):
        log.debug("Debug message")
        self.assertIn("Debug message", self.stdout.getvalue())
        self.assertIn("Debug message", self.test_log_file.read_text())

    def test_success_message(self):
        log.success("Success message")
        self.assertIn("Success message", self.stdout.getvalue())
        self.assertIn("Success message", self.test_log_file.read_text())

    def test_notify_message(self):
        log.notify("Notify message")
        self.assertIn("Notify message", self.stdout.getvalue())
        self.assertIn("Notify message", self.test_log_file.read_text())

    def test_info_message(self):
        log.info("Info message")
        self.assertIn("Info message", self.stdout.getvalue())
        self.assertIn("Info message", self.test_log_file.read_text())

    def test_warning_message(self):
        log.warning("Warning message")
        self.assertIn("Warning message", self.stdout.getvalue())
        self.assertIn("Warning message", self.test_log_file.read_text())

    def test_error_message(self):
        log.error("Error message")
        self.assertIn("Error message", self.stderr.getvalue())
        self.assertIn("Error message", self.test_log_file.read_text())

    def test_multiple_messages(self):
        log.info("First message")
        log.error("Second message")
        log.warning("Third message")

        stdout_content = self.stdout.getvalue()
        stderr_content = self.stderr.getvalue()
        file_content = self.test_log_file.read_text()

        self.assertIn("First message", stdout_content)
        self.assertIn("Third message", stdout_content)
        self.assertIn("Second message", stderr_content)
        self.assertIn("First message", file_content)
        self.assertIn("Second message", file_content)
        self.assertIn("Third message", file_content)

    def test_stream_redirection(self):
        new_stdout = io.StringIO()
        new_stderr = io.StringIO()
        log.set_stdout(new_stdout)
        log.set_stderr(new_stderr)

        log.info("Test stdout")
        log.error("Test stderr")

        self.assertIn("Test stdout", new_stdout.getvalue())
        self.assertIn("Test stderr", new_stderr.getvalue())

    def test_debug_level_config(self):
        # Test with debug disabled
        conf.set_debug(False)
        log.instance = None  # Reset logger
        log.debug("Hidden debug")
        self.assertEqual("", self.stdout.getvalue())

        # Test with debug enabled
        conf.set_debug(True)
        log.instance = None  # Reset logger
        log.debug("Visible debug")
        self.assertIn("Visible debug", self.stdout.getvalue())

    def test_log_file_creation(self):
        # Delete log file if exists
        if self.test_log_file.exists():
            self.test_log_file.unlink()

        # First log should create file
        self.assertFalse(self.test_log_file.exists())
        log.info("Create log file")
        self.assertTrue(self.test_log_file.exists())
        self.assertIn("Create log file", self.test_log_file.read_text())

    def test_debug_mode_filtering(self):
        # Test with debug mode off
        conf.set_debug(False)
        log.instance = None  # Reset logger to apply new debug setting

        log.debug("Debug message when off")
        log.info("Info message when off")

        stdout_off = self.stdout.getvalue()
        self.assertNotIn("Debug message when off", stdout_off)
        self.assertIn("Info message when off", stdout_off)

        # Clear buffers
        self.stdout.truncate(0)
        self.stdout.seek(0)

        # Test with debug mode on
        conf.set_debug(True)
        log.instance = None  # Reset logger to apply new debug setting

        log.debug("Debug message when on")
        log.info("Info message when on")

        stdout_on = self.stdout.getvalue()
        self.assertIn("Debug message when on", stdout_on)
        self.assertIn("Info message when on", stdout_on)

    def test_custom_levels_visibility(self):
        """Custom levels should print below DEBUG level"""
        # Test with debug mode off
        conf.set_debug(False)
        log.instance = None

        log.debug("Debug message when debug off")
        log.success("Success message when debug off")
        log.notify("Notify message when debug off")

        stdout_off = self.stdout.getvalue()
        self.assertNotIn("Debug message when debug off", stdout_off)
        self.assertIn("Success message when debug off", stdout_off)
        self.assertIn("Notify message when debug off", stdout_off)

        # Clear buffers
        self.stdout.truncate(0)
        self.stdout.seek(0)

        # Test with debug mode on
        conf.set_debug(True)
        log.instance = None

        log.debug("Debug message when debug on")
        log.success("Success message when debug on")
        log.notify("Notify message when debug on")

        stdout_on = self.stdout.getvalue()
        self.assertIn("Debug message when debug on", stdout_on)
        self.assertIn("Success message when debug on", stdout_on)
        self.assertIn("Notify message when debug on", stdout_on)
