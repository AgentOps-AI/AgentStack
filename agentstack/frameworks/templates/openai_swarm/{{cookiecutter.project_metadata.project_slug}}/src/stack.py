from swarm import Swarm, Agent
import agentstack


class {{ cookiecutter.project_metadata.class_name }}Stack:

    def run(self, inputs: list[str]):
        app = Swarm()
        history = []
        for task in agentstack.get_all_tasks():
            agentstack.log.notify(f"Running task `{task.name}`")
            response = app.run(
                agent=getattr(self, task.name)(), 
                messages=history, 
                context_variables=inputs, 
                debug=agentstack.conf.DEBUG, 
            )
            for message in response.messages:
                if message.get('role') not in ['user', 'assistant']:
                    continue
                if message.get('tool_calls'):
                    continue
                history.append(message)
                agentstack.log.info(message['content'])

