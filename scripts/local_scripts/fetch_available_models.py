from agentstack.providers import get_available_models, parse_provider_model


def main():
    print("\n=== Available LLM Models ===\n")

    # First fetch - will get from litellm or fallback to preferred models
    print("Fetching available models...")
    models = get_available_models()
    print(f"Found {len(models)} models")

    print("\nAvailable models:")
    for model in sorted(models):
        print(f"  - {model}")

    # Demonstrate caching
    print("\nFetching models again...")
    cached_models = get_available_models()
    print(f"Used cached result: {models is cached_models}")

    # Show how model strings are parsed
    print("\nExample model string parsing:")
    examples = [
        "openai/gpt-4",
        "anthropic/claude-3-opus",
        "openrouter/anthropic/claude-3",
    ]

    for model_id in examples:
        provider, model = parse_provider_model(model_id)
        print(f"\n{model_id}")
        print(f"  ├─ Provider: {provider}")
        print(f"  └─ Model: {model}")


if __name__ == "__main__":
    main()
