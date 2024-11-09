from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
import tools

@CrewBase
class TripplannerCrew():
	"""trip_planner crew"""

	# Agent definitions
	@agent
	def city_selection_expert(self) -> Agent:
		return Agent(
			config=self.agents_config['city_selection_expert'],
			tools=[tools.Browserbase, tools.Browserbase, tools.Browserbase, tools.Browserbase, tools.Browserbase, ],  # Pass in what tools this agent should have
			verbose=True
		)

	@agent
	def local_expert(self) -> Agent:
		return Agent(
			config=self.agents_config['local_expert'],
			tools=[tools.Browserbase, tools.Browserbase, tools.Browserbase, tools.Browserbase, tools.Browserbase, ],  # Pass in what tools this agent should have
			verbose=True
		)

	@agent
	def travel_concierge(self) -> Agent:
		return Agent(
			config=self.agents_config['travel_concierge'],
			tools=[tools.Browserbase, tools.Browserbase, tools.Browserbase, tools.Browserbase, tools.Browserbase, ],  # Pass in what tools this agent should have
			verbose=True
		)

	# Task definitions
	@task
	def identify_task(self) -> Task:
		return Task(
			config=self.tasks_config['identify_task'],
		)

	@task
	def gather_task(self) -> Task:
		return Task(
			config=self.tasks_config['gather_task'],
		)

	@task
	def plan_task(self) -> Task:
		return Task(
			config=self.tasks_config['plan_task'],
			output_file="itinerary.md"
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