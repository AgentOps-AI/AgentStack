from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
import tools

@CrewBase
class SentimentanalyserCrew():
    """sentiment_analyser crew"""

    # Agent definitions

    # Task definitions

    @agent
    def web_scraper(self) -> Agent:
        return Agent(
            config=self.agents_config['web_scraper'],
            tools=[tools.query_data], # add tools here or use `agentstack tools add <tool_name>
            verbose=True,
        )

    @agent
    def analyser(self) -> Agent:
        return Agent(
            config=self.agents_config['analyser'],
            tools=[], # add tools here or use `agentstack tools add <tool_name>
            verbose=True,
        )

    @task
    def scrape_data(self) -> Task:
        return Task(
            config=self.tasks_config['scrape_data'],
        )

    @task
    def sentiment_analysis(self) -> Task:
        return Task(
            config=self.tasks_config['sentiment_analysis'],
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