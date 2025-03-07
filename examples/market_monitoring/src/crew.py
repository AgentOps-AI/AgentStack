from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
import agentstack


@CrewBase
class MarketmonitoringCrew:
    """market_monitoring crew"""

    @agent
    def web_scraper(self) -> Agent:
        return Agent(
            config=self.agents_config["web_scraper"],
            tools=[
                *agentstack.tools["agentql"]
            ],  # add tools here or use `agentstack tools add <tool_name>
            verbose=True,
        )

    @agent
    def market_reporter(self) -> Agent:
        return Agent(
            config=self.agents_config["market_reporter"],
            tools=[],  # add tools here or use `agentstack tools add <tool_name>
            verbose=True,
        )

    @task
    def scrape_site(self) -> Task:
        return Task(
            config=self.tasks_config["scrape_site"],
        )

    @task
    def report(self) -> Task:
        return Task(
            config=self.tasks_config["report"],
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Test crew"""
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
        )
