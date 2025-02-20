from typing import Optional
from art import text2art
import questionary
from agentstack import conf, log
from agentstack.conf import ConfigFile
from agentstack.utils import is_snake_case
from agentstack.generation import InsertionPoint
from agentstack import repo
from agentstack.providers import get_available_models


def welcome_message():
    title = text2art("AgentStack", font="smisome1")
    tagline = "The easiest way to build a robust agent application!"
    border = "-" * len(tagline)

    # Print the welcome message with ASCII art
    log.info(title)
    log.info(border)
    log.info(tagline)
    log.info(border)


def undo() -> None:
    """Undo the last committed changes."""
    conf.assert_project()

    changed_files = repo.get_uncommitted_files()
    if changed_files:
        log.warning("There are uncommitted changes that may be overwritten.")
        for changed in changed_files:
            log.info(f" - {changed}")

        should_continue = questionary.confirm(
            "Do you want to continue?",
            default=False,
        ).ask()

        if not should_continue:
            return

    repo.revert_last_commit(hard=True)


def configure_default_model():
    """Set the default model"""
    agentstack_config = ConfigFile()
    if agentstack_config.default_model:
        log.debug("Using default model from project config.")
        return  # Default model already set

    log.info("Project does not have a default model configured.")

    available_models = get_available_models()

    other_msg = "Other (enter a model name)"
    model = questionary.select(
        "Which model would you like to use?",
        choices=available_models + [other_msg],
        use_indicator=True,
        use_search_filter=True,
    ).ask()

    if model == other_msg:
        log.info('A list of available models is available at: "https://docs.litellm.ai/docs/providers"')
        model = questionary.text("Enter the model name:").ask()

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

        def validate(text: str) -> bool:
            if min_length and len(text) < min_length:
                return False
            if snake_case and not is_snake_case(text):
                return False
            if validate_func and not validate_func(text):
                return False
            return True

        value = questionary.text(
            message,
            validate=validate if validate_func or min_length or snake_case else None,
        ).ask()

        if value:
            return value


def parse_insertion_point(position: Optional[str] = None) -> Optional[InsertionPoint]:
    """
    Parse an insertion point CLI argument into an InsertionPoint enum.
    """
    if position is None:
        return None  # defer assumptions

    valid_positions = {x.value for x in InsertionPoint}
    if position not in valid_positions:
        raise ValueError(f"Position must be one of {','.join(valid_positions)}.")

    return next(x for x in InsertionPoint if x.value == position)
