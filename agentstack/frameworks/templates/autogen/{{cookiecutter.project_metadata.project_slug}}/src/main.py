from typing import Annotated, Literal

import agentops

from autogen import ConversableAgent, UserProxyAgent, config_list_from_json, register_function

agentops.init(default_tags=['autogen', 'agentstack'])


def main():
    # Load LLM inference endpoints from an env variable or a file
    # See https://microsoft.github.io/autogen/docs/FAQ#set-your-api-endpoints
    # and OAI_CONFIG_LIST_sample.
    # For example, if you have created a OAI_CONFIG_LIST file in the current working directory, that file will be used.
    config_list = config_list_from_json(env_or_file="OAI_CONFIG_LIST")

    {%- for agent in cookiecutter.structure.agents %}

    {{agent.name}}_agent = ConversableAgent(
        name="{{agent.name}}",
        system_message="""
    role:
      {{agent.role}}
    goal:
      {{agent.goal}}
    backstory:
      {{agent.backstory}}
        """,
        llm_config={"config_list": config_list},  # TODO: support other models
    )
    {%- endfor %}

    # # The user proxy agent is used for interacting with the assistant agent
    # # and executes tool calls.
    user_proxy = ConversableAgent(
        name="User",
        llm_config=False,
        is_termination_msg=lambda msg: msg.get("content") is not None and "TERMINATE" in msg["content"],
        human_input_mode="NEVER",
    )

    # TODO: use this as tool add example
    # assistant.register_for_llm(name="calculator", description="A simple calculator")(calculator)
    # user_proxy.register_for_execution(name="calculator")(calculator)

    # Register the calculator function to the two agents.
    # register_function(
    #     calculator,
    #     caller=assistant,  # The assistant agent can suggest calls to the calculator.
    #     executor=user_proxy,  # The user proxy agent can execute the calculator calls.
    #     name="calculator",  # By default, the function name is used as the tool name.
    #     description="A simple calculator",  # A description of the tool.
    # )

    # Let the assistant start the conversation.  It will end when the user types exit.
    # user_proxy.initiate_chat(assistant, message="What is (1423 - 123) / 3 + (32 + 23) * 5?")

    agentops.end_session("Success")


if __name__ == "__main__":
    main()