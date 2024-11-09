from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
import tools


@CrewBase
class WebscraperCrew():
    """web_scraper crew"""

    # Agent definitions
    @agent
    def summarizer(self) -> Agent:
        return Agent(
            config=self.agents_config['summarizer'],
            tools=[tools.write_to_memory, tools.read_from_memory, ],
            # add tools here or use `agentstack tools add <tool_name>
            verbose=True
        )

    @agent
    def scraper(self) -> Agent:
        return Agent(
            config=self.agents_config['scraper'],
            tools=[tools.write_to_memory, tools.read_from_memory],
            # add tools here or use `agentstack tools add <tool_name>
            verbose=True
        )

    # Task definitions
    @task
    def scrape_site(self) -> Task:
        return Task(
            config=self.tasks_config['scrape_site'],
        )

    @task
    def summarize_content(self) -> Task:
        return Task(
            config=self.tasks_config['summarize_content'],
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
