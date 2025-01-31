import os, sys
from art import text2art
import inquirer
from agentstack import conf, log
from agentstack.conf import ConfigFile
from agentstack.exceptions import ValidationError
from agentstack.utils import validator_not_empty, is_snake_case


PREFERRED_MODELS = [
    'groq/deepseek-r1-distill-llama-70b',
    'deepseek/deepseek-chat',
    'deepseek/deepseek-coder',
    'deepseek/deepseek-reasoner',
    'openai/gpt-4o',
    'anthropic/claude-3-5-sonnet',
    'openai/o1-preview',
    'openai/gpt-4-turbo',
    'anthropic/claude-3-opus',
]


def welcome_message():
    title = text2art("AgentStack", font="smisome1")
    tagline = "The easiest way to build a robust agent application!"
    border = "-" * len(tagline)

    # Print the welcome message with ASCII art
    log.info(title)
    log.info(border)
    log.info(tagline)
    log.info(border)


def configure_default_model():
    """Set the default model"""
    agentstack_config = ConfigFile()
    if agentstack_config.default_model:
        log.debug("Using default model from project config.")
        return  # Default model already set

    log.info("Project does not have a default model configured.")
    other_msg = "Other (enter a model name)"
    model = inquirer.list_input(
        message="Which model would you like to use?",
        choices=PREFERRED_MODELS + [other_msg],
    )

    if model == other_msg:  # If the user selects "Other", prompt for a model name
        log.info('A list of available models is available at: "https://docs.litellm.ai/docs/providers"')
        model = inquirer.text(message="Enter the model name")

    log.debug("Writing default model to project config.")
    with ConfigFile() as agentstack_config:
        agentstack_config.default_model = model


def get_validated_input(
    message: str,
    validate_func=None,
    min_length: int = 0,
    snake_case: bool = False,
) -> str:
    """Helper function to get validated input from user.

    Args:
        message: The prompt message to display
        validate_func: Optional custom validation function
        min_length: Minimum length requirement (0 for no requirement)
        snake_case: Whether to enforce snake_case naming
    """
    while True:
        value = inquirer.text(
            message=message,
            validate=validate_func or validator_not_empty(min_length) if min_length else None,
        )
        if snake_case and not is_snake_case(value):
            raise ValidationError("Input must be in snake_case")
        return value

