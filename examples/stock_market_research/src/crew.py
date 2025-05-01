from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
import agentstack

@CrewBase
class StockmarketresearchCrew():
    """stock_market_research crew"""

    @agent
    def web_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['web_researcher'],
            tools = [
                get_dappier_tool("real_time_web_search")
            ],
            verbose=True,
        )

    @agent
    def stock_insights_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['stock_insights_analyst'],
            tools = [
                get_dappier_tool("stock_market_data_search")
            ],
            verbose=True,
        )

    @agent
    def report_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['report_analyst'],
            verbose=True,
        )

    @task
    def company_overview(self) -> Task:
        return Task(
            config=self.tasks_config['company_overview'],
        )

    @task
    def financials_performance(self) -> Task:
        return Task(
            config=self.tasks_config['financials_performance'],
        )

    @task
    def competitive_benchmarking(self) -> Task:
        return Task(
            config=self.tasks_config['competitive_benchmarking'],
        )

    @task
    def real_time_stock_snapshot(self) -> Task:
        return Task(
            config=self.tasks_config['real_time_stock_snapshot'],
        )

    @task
    def news_and_sentiment(self) -> Task:
        return Task(
            config=self.tasks_config['news_and_sentiment'],
        )

    @task
    def generate_investment_report(self) -> Task:
        return Task(
            config=self.tasks_config['generate_investment_report'],
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Test crew"""
        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
        )


def get_dappier_tool(tool_name: str):
        for tool in agentstack.tools["dappier"]:
            if tool.name == tool_name:
                return tool
        return None
