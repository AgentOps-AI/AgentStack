from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
import tools


@CrewBase
class WebresearcherCrew():
    """web_researcher crew"""

    # Agent definitions
    @agent
    def content_summarizer(self) -> Agent:
        return Agent(
            config=self.agents_config['content_summarizer'],
            tools=[],  # add tools here or use `agentstack tools add <tool_name>
            verbose=True
        )

    @agent
    def web_scraper(self) -> Agent:
        return Agent(
            config=self.agents_config['web_scraper'],
            tools=[tools.web_scrape],  # add tools here or use `agentstack tools add <tool_name>
            verbose=True
        )

    @agent
    def content_storer(self) -> Agent:
        return Agent(
            config=self.agents_config['content_storer'],
            tools=[tools.create_database, tools.execute_sql_ddl, tools.run_sql_query],  # add tools here or use `agentstack tools add <tool_name>
            verbose=True
        )

    # Task definitions
    @task
    def scrape_site(self) -> Task:
        return Task(
            config=self.tasks_config['scrape_site'],
        )

    @task
    def summarize(self) -> Task:
        return Task(
            config=self.tasks_config['summarize'],
        )

    @task
    def store(self) -> Task:
        return Task(
            config=self.tasks_config['store'],
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