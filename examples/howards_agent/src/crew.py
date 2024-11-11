from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
import tools

@CrewBase
class HowardsagentCrew():
	"""howards_agent crew"""

	# Agent definitions
	@agent
	def agent1(self) -> Agent:
		return Agent(
			config=self.agents_config['agent1'],
			tools=[*tools.composio_tools,],  # Pass in what tools this agent should have
			verbose=True
		)

	# Task definitions
	@task
	def new_task(self) -> Task:
	    return Task(
	        config=self.tasks_config['new_task'],
	    )
	
	@task
	def task1(self) -> Task:
		return Task(
			config=self.tasks_config['task1'],
		)

	@crew
	def crew(self) -> Crew:
		"""Creates the Test crew"""
		return Crew(
			agents=self.agents, # Automatically created by the @agent decorator
			tasks=self.tasks, # Automatically created by the @task decorator
			process=Process.sequential,
			verbose=True,
			# process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
		)
