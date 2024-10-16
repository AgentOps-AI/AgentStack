import unittest

from agentstack.utils import clean_input


class TestUtils(unittest.TestCase):
    def test_clean_input_no_change(self):
        cleaned = clean_input('test_project')
        self.assertEqual('test_project', cleaned)

    def test_clean_input_remove_space(self):
        cleaned = clean_input('test project')
        self.assertEqual('test_project', cleaned)