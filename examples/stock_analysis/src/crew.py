from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
import tools


@CrewBase
class StockanalysisCrew():
    """stock_analysis crew"""

    # Agent definitions
    @agent
    def analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['analyst'],
            tools=[],  # add tools here or use `agentstack tools add <tool_name>
            verbose=True
        )

    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['researcher'],
            tools=[tools.query_perplexity, ],  # add tools here or use `agentstack tools add <tool_name>
            verbose=True
        )

    # Task definitions
    @task
    def research_stock(self) -> Task:
        return Task(
            config=self.tasks_config['research_stock'],
        )

    @task
    def buy_sell_decision(self) -> Task:
        return Task(
            config=self.tasks_config['buy_sell_decision'],
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
