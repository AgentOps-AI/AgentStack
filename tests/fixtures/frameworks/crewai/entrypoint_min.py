from crewai import Crew, Process
from crewai.project import CrewBase, crew


@CrewBase
class TestCrew:
    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
