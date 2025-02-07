from typing import Optional, Any, Callable
from pathlib import Path
import ast
from agentstack import conf, log
from agentstack.exceptions import ValidationError
from agentstack.generation import InsertionPoint
from agentstack.frameworks import Provider, BaseEntrypointFile
from agentstack._tools import ToolConfig
from agentstack.tasks import TaskConfig
from agentstack.agents import AgentConfig
from agentstack.generation import asttools
from agentstack import graph

NAME: str = "LLamaIndex"
ENTRYPOINT: Path = Path('src/stack.py')

PROVIDERS = {
    'openai': Provider(
        class_name='OpenAI',
        module_name='llama_index.llms.openai',
        dependencies=['llama-index-llms-openai', 'llama-index-agent-openai'],
    ), 
    'anthropic': Provider(
        class_name='Anthropic',
        module_name='llama_index.llms.anthropic',
        dependencies=['llama-index-llms-anthropic'],
    ),
    'deepseek': Provider(
        class_name='DeepSeek',
        module_name='llama_index.llms.deepseek',
        dependencies=['llama-index-llms-deepseek'],
    ),
    'google': Provider(
        class_name='Gemini',
        module_name='llama_index.llms.gemini',
        dependencies=['llama-index-llms-gemini'],
    ),
    'huggingface': Provider(
        class_name='HuggingFaceLLM',
        module_name='llama_index.llms.huggingface',
        dependencies=['llama-index-llms-huggingface'],
    ),
    'microsoft': Provider(
        class_name='AzureOpenAI',
        module_name='llama_index.llms.azure',
        dependencies=['llama-index-llms-azure-openai'],
    ),
    'mistral': Provider(
        class_name='MistralAI',
        module_name='llama_index.llms.mistralai',
        dependencies=['llama-index-llms-mistralai'],
    ),
    'ollama': Provider(
        class_name='Ollama',
        module_name='llama_index.llms.ollama',
        dependencies=['llama-index-llms-ollama'],
    ),
    'groq': Provider(
        class_name='Groq',
        module_name='llama_index.llms.groq',
        dependencies=['llama-index-llms-groq'],
    ),
    'openrouter': Provider(
        class_name='OpenRouter',
        module_name='llama_index.llms.openrouter',
        dependencies=['llama-index-llms-openrouter'],
    ),
}


class LlamaIndexFile(BaseEntrypointFile):
    """
    Parses and manipulates the entrypoint file.
    All AST interactions should happen within the methods of this class.
    """

    def get_new_task_method(self, task: TaskConfig) -> str:
        """Get the content of a new task method."""
        return f"""    @agentstack.task
    def {task.name}(self) -> ChatMessage:
        task_config = agentstack.get_task('{task.name}')
        return ChatMessage(role="user", content=task_config.prompt)"""

    def get_new_agent_method(self, agent: AgentConfig) -> str:
        """Get the content of a new agent method."""
        assert agent.provider in PROVIDERS.keys()  # this gets validated in `add_agent`
        llm_class_name = PROVIDERS[agent.provider].class_name
        return f"""    @agentstack.agent
    def {agent.name}(self) -> FunctionAgent:
        agent_config = agentstack.get_agent('{agent.name}')
        llm = {llm_class_name}(
            model=agent_config.model, 
        )
        return FunctionAgent(
            name=agent_config.name, 
            description=agent_config.role, 
            system_prompt=agent_config.prompt, 
            llm=llm, 
            tools=[], 
        )"""

    def get_agent_tools(self, agent_name: str) -> ast.List:
        """Get the list of tools used by an agent as an AST List node."""
        method = asttools.find_method(self.get_agent_methods(), agent_name)
        if method is None:
            raise ValidationError(f"Method `{agent_name}` does not exist in {ENTRYPOINT}")

        agent_class = asttools.find_class_instantiation(method, 'FunctionAgent')
        if agent_class is None:
            raise ValidationError(f"Method `{agent_name}` does not call `FunctionAgent` in {ENTRYPOINT}")

        tools_kwarg = asttools.find_kwarg_in_method_call(agent_class, 'tools')
        if not tools_kwarg:
            raise ValidationError(f"`FunctionAgent` does not have a kwarg `tools` in {ENTRYPOINT}")

        if not isinstance(tools_kwarg.value, ast.List):
            raise ValidationError(f"`FunctionAgent` must define a list for kwarg `tools` in {ENTRYPOINT}")

        return tools_kwarg.value


def get_entrypoint() -> LlamaIndexFile:
    """Get the entrypoint file."""
    return LlamaIndexFile(conf.PATH / ENTRYPOINT)


def validate_project() -> None:
    """
    Validate that the project is ready to run.
    Raises an `agentstack.ValidationError` if the project is not valid.
    """
    return  # No additional validation needed.


def add_task(task: TaskConfig, position: Optional[InsertionPoint] = None) -> None:
    """
    Add a task method to the entrypoint.
    """
    if position is not None:
        raise NotImplementedError(f"Task insertion points are not supported in {NAME}.")

    with get_entrypoint() as entrypoint:
        entrypoint.add_task_method(task)


def add_agent(agent: AgentConfig, position: Optional[InsertionPoint] = None) -> None:
    """
    Add an agent method to the entrypoint.
    """
    if position is not None:
        raise NotImplementedError(f"Agent insertion points are not supported in {NAME}.")

    # individual LLM providers rely on additional dependencies, install them
    try:
        provider = PROVIDERS[agent.provider]
        provider.install_dependencies()
    except KeyError:
        raise ValidationError(
            f"{NAME} provider '{agent.provider}' has not been implemented. "
            f"AgentStack currently supports: {', '.join(PROVIDERS.keys())} "
        )

    with get_entrypoint() as entrypoint:
        # also include an import statement for the LLM provider
        if not entrypoint.get_import(provider.module_name, provider.class_name):
            entrypoint.add_import(provider.module_name, provider.class_name)

        entrypoint.add_agent_method(agent)


def add_tool(tool: ToolConfig, agent_name: str):
    """
    Add a tool to the entrypoint for the specified agent.
    """
    with get_entrypoint() as entrypoint:
        entrypoint.add_agent_tools(agent_name, tool)


def remove_tool(tool: ToolConfig, agent_name: str):
    """
    Remove a tool from the entrypoint for the specified agent.
    """
    with get_entrypoint() as entrypoint:
        entrypoint.remove_agent_tools(agent_name, tool)


def wrap_tool(tool_func: Callable) -> Callable:
    """
    Wrap a tool function with framework-specific functionality.
    """
    # TODO llamaindex does have a BaseTool class, but I don't see what additional
    # value we offer by wrapping tools in it.
    return tool_func


def get_graph() -> list[graph.Edge]:
    """Get the graph of the user's project."""
    log.debug(f"{NAME} does not support graph generation.")
    return []
