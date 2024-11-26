from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
import tools

@CrewBase
class JobpostingCrew():
    """job_posting crew"""

    # Agent definitions
    @agent
    def review_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['review_agent'],
            tools=[tools.web_scrape, tools.web_crawl, tools.retrieve_web_crawl, ],  # add tools here or use `agentstack tools add <tool_name>
            verbose=True
        )
    
    @agent
    def writer_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['writer_agent'],
            tools=[tools.web_scrape, tools.web_crawl, tools.retrieve_web_crawl, ],  # add tools here or use `agentstack tools add <tool_name>
            verbose=True
        )
    
    @agent
    def researcher_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['research_agent'],
            tools=[tools.web_scrape, tools.web_crawl, tools.retrieve_web_crawl, ],  # add tools here or use `agentstack tools add <tool_name>
            verbose=True
        )
    

    # Task definitions
    @task
    def research_company_culture_task(self) -> Task:
        return Task(
            config=self.tasks_config['research_company_culture_task'],
        )

    @task
    def research_role_requirements_task(self) -> Task:
        return Task(
            config=self.tasks_config['research_role_requirements_task'],
        )

    @task
    def draft_job_posting_task(self) -> Task:
        return Task(
            config=self.tasks_config['draft_job_posting_task'],
        )

    @task
    def review_and_edit_job_posting_task(self) -> Task:
        return Task(
            config=self.tasks_config['review_and_edit_job_posting_task'],
        )

    @task
    def industry_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['industry_analysis_task'],
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Test crew"""
        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            # process=Process.sequential,
            verbose=True,
            process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        	manager_llm='openai/gpt-4o'
        )