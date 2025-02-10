from typing import Optional
import re
import pydantic
from agentstack.exceptions import ValidationError

# model ids follow LiteLLM format
PREFERRED_MODELS = {
    'groq/deepseek-r1-distill-llama-70b': {
        'name': "DeepSeek R1 Distill Llama 70B",
        'host': "Groq",
        'description': "The Groq DeepSeek R1 Distill Llama 70B model",
    },
    'deepseek/deepseek-reasoner': {
        'name': "DeepSeek Reasoner",
        'host': "DeepSeek",
        'description': "The DeepSeek Reasoner model hosted by DeepSeek",
    },
    'openai/o1-preview': {
        'name': "o1 Preview",
        'host': "OpenAI",
        'description': "The OpenAI o1 Preview model",
    },
    'anthropic/claude-3-5-sonnet': {
        'name': "Claude 3.5 Sonnet",
        'host': "Anthropic",
        'description': "The Anthropic Claude 3.5 Sonnet model",
    },
    # TODO there is no publicly available OpenRouter implementation for
    # LangChain, so we can't recommend this yet.
    # 'openrouter/deepseek/deepseek-r1': {
    #     'name': "DeepSeek R1",
    #     'host': "OpenRouter",
    #     'description': "The DeepSeek R1 model hosted by OpenRouter",
    # },
    'openai/gpt-4o': {
        'name': "GPT-4o",
        'host': "OpenAI",
        'description': "The OpenAI GPT-4o model",
    },
    'anthropic/claude-3-opus': {
        'name': "Claude 3 Opus",
        'host': "Anthropic",
        'description': "The Anthropic Claude 3 Opus model",
    },
}


class ProviderConfig(pydantic.BaseModel):
    id: str
    name: Optional[str]
    host: Optional[str]
    description: Optional[str]
    provider = property(lambda self: parse_provider_model(self.id)[0])
    model = property(lambda self: parse_provider_model(self.id)[1])


def get_preferred_models() -> list[ProviderConfig]:
    return [ProviderConfig(id=model_id, **model) for model_id, model in PREFERRED_MODELS.items()]


def get_preferred_model_ids() -> list[str]:
    return [model.id for model in get_preferred_models()]


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
