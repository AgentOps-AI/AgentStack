from agentstack.providers import get_available_models, parse_provider_model


def main():
    print("\n=== Testing Model Provider Functions ===\n")

    # Test get_available_models()
    print("Getting available models (first call)...")
    models = get_available_models()
    print(f"Found {len(models)} models")
    print("\nFirst 5 models:")
    for model in sorted(models)[:5]:
        print(f"  - {model}")

    # Test caching
    print("\nGetting models again (should be cached)...")
    cached_models = get_available_models()
    print(f"Models are same object: {models is cached_models}")

    # Test parse_provider_model()
    print("\nTesting provider/model parsing:")
    test_cases = [
        "openai/gpt-4",
        "anthropic/claude-3-opus",
        "openrouter/anthropic/claude-3",
    ]

    for model_id in test_cases:
        provider, model = parse_provider_model(model_id)
        print(f"\nParsing: {model_id}")
        print(f"  Provider: {provider}")
        print(f"  Model: {model}")


if __name__ == "__main__":
    main()
