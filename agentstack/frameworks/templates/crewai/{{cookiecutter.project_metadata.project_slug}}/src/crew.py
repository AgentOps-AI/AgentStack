from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
import agentstack

@CrewBase
class {{cookiecutter.project_metadata.project_name|replace('-', '')|replace('_', '')|capitalize}}Crew():
    """{{cookiecutter.project_metadata.project_name}} crew"""

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