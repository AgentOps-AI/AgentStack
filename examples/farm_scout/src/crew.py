from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
import tools


@CrewBase
class FarmscoutCrew:
    """farm_scout crew"""

    # Agent definitions
    @agent
    def scout(self) -> Agent:
        return Agent(
            config=self.agents_config["scout"],
            tools=[
                tools.get_farm_land
            ],  # add tools here or use `agentstack tools add <tool_name>
            verbose=True,
        )

    @task
    def find_farms(self) -> Task:
        return Task(
            config=self.tasks_config["find_farms"],
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Test crew"""
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
