from swarm import Swarm, Agent
import agentstack


class {{ cookiecutter.project_metadata.project_name|replace('-', '')|replace('_', '')|capitalize }}Stack:

    def _handoff(self, task_name: str):
        """Return a task formatted as a tool for handing off to another agent."""
        task = getattr(self, task_name)
        def func(messages: list[str] = []) -> Agent:
            return task(messages=messages)
        func.__name__ = task_name
        return func

    def _get_first_task(self) -> Agent:
        """Get the first task."""
        task_name = agentstack.get_all_task_names()[0]
        return getattr(self, task_name)()

    def run(self, inputs: list[str]):
        app = Swarm()
        response = app.run(
            agent=self._get_first_task(), 
            messages=[], 
            context_variables=inputs, 
            debug=agentstack.conf.DEBUG, 
        )

        for message in response.messages:
            if message.get('tool_calls'):
                for tool_call in message['tool_calls']:
                    agentstack.log.notify(f"Calling tool `{tool_call['function']['name']}`")
                    agentstack.log.debug(tool_call['function']['arguments'])
            elif message.get('role') != 'tool':
                agentstack.log.notify(f"{message['role']}:")
                agentstack.log.info(message['content'])

