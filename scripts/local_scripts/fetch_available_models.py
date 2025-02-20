import litellm
import json


def main():
    print("\n=== Available LLM Models ===\n")

    print(f"Total models: {len(litellm.model_list)}")

    print("\n=== Models By Provider ===\n")
    for provider, models in litellm.models_by_provider.items():
        print(f"\n{provider.upper()}:")
        for model in sorted(models):
            print(f"  - {model}")

    output = {"all_models": litellm.model_list, "models_by_provider": litellm.models_by_provider}

    with open("available_models.json", "w") as f:
        json.dump(output, f, indent=2)
    print("\nSaved complete model list to available_models.json")


if __name__ == "__main__":
    main()
