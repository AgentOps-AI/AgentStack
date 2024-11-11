import unittest

from agentstack.utils import clean_input, is_snake_case


class TestUtils(unittest.TestCase):
    def test_clean_input_no_change(self):
        cleaned = clean_input('test_project')
        self.assertEqual('test_project', cleaned)

    def test_clean_input_remove_space(self):
        cleaned = clean_input('test project')
        self.assertEqual('test_project', cleaned)

    def test_is_snake_case(self):
        assert is_snake_case("hello_world")
        assert not is_snake_case("HelloWorld")
        assert not is_snake_case("Hello-World")
        assert not is_snake_case("hello-world")
        assert not is_snake_case("hello world")
