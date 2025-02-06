from agentstack.exceptions import ValidationError


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

