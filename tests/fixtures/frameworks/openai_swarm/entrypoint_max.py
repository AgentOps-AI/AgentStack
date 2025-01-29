from swarm import Swarm, Agent
import agentstack


class TestStack:

    def _handoff(self, agent_name: str):
        """Tool for handing off to another agent."""
        agent = getattr(self, agent_name)
        def func(context_variables: list[str]):
            return agent(context_variables)
        return func

    def _get_first_task(self):
        """Get the first task."""
        task_name = agentstack.get_all_task_names()[0]
        return getattr(self, task_name)()

    @agentstack.agent
    def agent_name(self, messages: list[str] = []):
        agent_config = agentstack.get_agent('agent_name')
        return Agent(
            name=agent_config.name, 
            model=agent_config.model, 
            instructions="\n".join([agent_config.prompt, *messages, ]),
            functions=[],
        )

    @agentstack.task
    def task_name(self):
        task_config = agentstack.get_task('task_name')
        messages = [
            task_config.prompt, 
        ]
        agent = getattr(self, task_config.agent)
        return agent(messages)

    def run(self, inputs: list[str]):
        app = Swarm()
        response = app.run(
            agent=self._get_first_task(), 
            messages=[], 
            context_variables=inputs, 
            debug=agentstack.conf.DEBUG, 
        )

        for message in response.messages:
            agentstack.log.info(message['content'])

