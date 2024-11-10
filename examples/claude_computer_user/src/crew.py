from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
import tools

@CrewBase
class ClaudecomputeruserCrew():
	"""claude_computer_user crew"""

	# Agent definitions
	@agent
	def claude_computer_agent(self) -> Agent:
	    return Agent(
	        config=self.agents_config['claude_computer_agent'],
	        tools=[tools.start_claude_computer_use, ],  # add tools here or use `agentstack tools add <tool_name>
	        verbose=True
	    )
	

	# Task definitions
	@task
	def start_docker_container(self) -> Task:
		return Task(
	        config=self.tasks_config['start_docker_container'],
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