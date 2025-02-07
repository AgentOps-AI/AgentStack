import unittest
from agentstack.exceptions import ValidationError
from agentstack.providers import (
    parse_provider_model, 
)


class ProvidersTest(unittest.TestCase):
    def test_parse_provider_model(self):
        cases = [
            "deepseek/deepseek-reasoner",
            "openrouter/deepseek/deepseek-r1",
            "openai/gpt-4o",
            "anthropic/claude-3-opus",
            "provider/model",
        ]
        expected = [
            ("deepseek", "deepseek-reasoner"),
            ("openrouter/deepseek", "deepseek-r1"),
            ("openai", "gpt-4o"),
            ("anthropic", "claude-3-opus"),
            ("provider", "model"),
        ]
        for case, expect in zip(cases, expected):
            self.assertEqual(parse_provider_model(case), expect)

    def test_invalid_provider_model(self):
        with self.assertRaises(ValidationError):
            parse_provider_model("invalid_provider_model")

