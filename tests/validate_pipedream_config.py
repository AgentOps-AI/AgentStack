from agentstack.tools import ToolConfig


def validate_pipedream_config():
    try:
        tool_conf = ToolConfig.from_tool_name("pipedream")
        print("Successfully loaded tool config:")
        print(f"Name: {tool_conf.name}")
        print(f"Category: {tool_conf.category}")
        print(f"Tools: {tool_conf.tools}")
        return True
    except Exception as e:
        print(f"Error loading tool config: {str(e)}")
        return False


if __name__ == "__main__":
    success = validate_pipedream_config()
    exit(0 if success else 1)
