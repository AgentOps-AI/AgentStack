import unittest

from agentstack.utils import clean_input, is_snake_case, validator_not_empty
from inquirer import errors as inquirer_errors


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

    def test_validator_not_empty(self):
        validator = validator_not_empty(min_length=1)
        
        # Valid input should return True
        self.assertTrue(validator(None, "test"))
        self.assertTrue(validator(None, "a"))
        
        # Empty input should raise ValidationError        
        with self.assertRaises(inquirer_errors.ValidationError):
            validator(None, "")
            
        # Test with larger min_length
        validator = validator_not_empty(min_length=3)
        self.assertTrue(validator(None, "test"))
        with self.assertRaises(inquirer_errors.ValidationError):
            validator(None, "ab")

