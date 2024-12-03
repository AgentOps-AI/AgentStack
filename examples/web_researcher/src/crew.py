from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
import tools


@CrewBase
class WebresearcherCrew:
    """web_researcher crew"""

    @agent
    def content_summarizer(self) -> Agent:
        return Agent(
            config=self.agents_config["content_summarizer"], tools=[], verbose=True
        )

    @agent
    def web_scraper(self) -> Agent:
        return Agent(
            config=self.agents_config["web_scraper"],
            tools=[tools.web_scrape],
            verbose=True,
        )

    @agent
    def content_storer(self) -> Agent:
        return Agent(
            config=self.agents_config["content_storer"],
            tools=[tools.create_database, tools.execute_sql_ddl, tools.run_sql_query],
            verbose=True,
        )

    @task
    def scrape_site(self) -> Task:
        return Task(config=self.tasks_config["scrape_site"])

    @task
    def summarize(self) -> Task:
        return Task(config=self.tasks_config["summarize"])

    @task
    def store(self) -> Task:
        return Task(config=self.tasks_config["store"])

    @crew
    def crew(self) -> Crew:
        """Creates the Test crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
