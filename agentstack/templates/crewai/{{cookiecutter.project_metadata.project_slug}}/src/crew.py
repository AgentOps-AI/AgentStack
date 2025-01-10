from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
import agentstack

@CrewBase
class {{cookiecutter.project_metadata.project_name|replace('-', '')|replace('_', '')|capitalize}}Crew():
    """{{cookiecutter.project_metadata.project_name}} crew"""

    # Agent definitions
    {%- for agent in cookiecutter.structure.agents %}
    {% if not agent.name == cookiecutter.structure.manager_agent %}@agent{% endif %}
    def {{agent.name}}(self) -> Agent:
        return Agent(
            config=self.agents_config['{{ agent.name }}'],
            tools=[],  # Pass in what tools this agent should have
            verbose=True,
            {% if agent.allow_delegation %}allow_delegation=True{% endif %}
        )
    {%- endfor %}

    # Task definitions
    {%- for task in cookiecutter.structure.tasks %}
    @task
    def {{task.name}}(self) -> Task:
        return Task(
            config=self.tasks_config['{{task.name}}'],
        )
    {%- endfor %}

    @crew
    def crew(self) -> Crew:
        """Creates the Test crew"""
        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.{{cookiecutter.structure.method}},
            {% if cookiecutter.structure.manager_agent %}manager_agent=self.{{cookiecutter.structure.manager_agent}}(),{% endif %}
            verbose=True,
        )