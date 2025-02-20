from agentstack.exceptions import ValidationError
import litellm
from typing import List
from functools import lru_cache

PROVIDER_ALIASES = {
    'openai': 'openai',
    'anthropic': 'anthropic',
    'groq': 'groq',
    'deepseek': 'deepseek',
    'mistral': 'mistral',
    'google': 'google',
    'huggingface': 'huggingface',
    'ollama': 'ollama',
}

# Fallback models if litellm.model_cost is empty or fails
# Perhaps useful for an offline mode for people with tons of storage and no internet
# Think: Government "quiet" rooms etc.
PREFERRED_MODELS = [
    'groq/deepseek-r1-distill-llama-70b',
    'deepseek/deepseek-chat',
    'deepseek/deepseek-coder',
    'deepseek/deepseek-reasoner',
    'openai/gpt-4o',
    'anthropic/claude-3-5-sonnet',  # this has the wrong name, fixed on my other branch.
    'openai/o1-preview',
    'openai/gpt-4-turbo',
    'anthropic/claude-3-opus',
]


@lru_cache(maxsize=1)
def get_available_models() -> List[str]:
    """
    Get list of available models in provider/model format.
    Results are cached to avoid processing litellm.model_cost multiple times.
    Falls back to PREFERRED_MODELS if no models found from litellm.
    """
    models = []

    try:
        for model_name in litellm.model_cost:
            if (
                isinstance(model_name, tuple)
                or not isinstance(model_name, str)
                or not any(p in model_name.lower() for p in PROVIDER_ALIASES.values())
            ):
                continue

            provider = next((p for p in PROVIDER_ALIASES.values() if p in model_name.lower()), None)

            if provider:
                models.append(f"{provider}/{model_name}")
    except Exception:
        # If anything goes wrong parsing litellm models, fall back to preferred models
        pass

    # If no models found from litellm, use preferred models
    if not models:
        models = PREFERRED_MODELS.copy()

    return sorted(models)


def parse_provider_model(model_id: str) -> tuple[str, str]:
    """Parse the provider and model name from the model ID"""
    # most providers are in the format "<provider>/<model-name>"
    # openrouter models are in the format "openrouter/<provider>/<model-name>"
    parts = tuple(model_id.split('/'))
    if len(parts) == 2:
        return parts
    elif len(parts) == 3:
        return '/'.join(parts[:2]), parts[2]
    else:
        raise ValidationError(f"Model id '{model_id}' does not match expected format.")
