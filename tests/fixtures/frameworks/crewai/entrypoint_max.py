from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
import tools


@CrewBase
class TestCrew:
    @agent
    def agent_name(self) -> Agent:
        return Agent(config=self.agents_config['agent_name'], tools=[], verbose=True)

    @task
    def task_name(self) -> Task:
        return Task(
            config=self.tasks_config['task_name'],
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
