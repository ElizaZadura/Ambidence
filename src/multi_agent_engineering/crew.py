from typing import List

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task

from multi_agent_engineering.models.build_plan import BuildPlan
from multi_agent_engineering.models.design_pack import DesignPack
from multi_agent_engineering.models.spec_pack import SpecPack


@CrewBase
class MultiAgentEngineering():
    """MultiAgentEngineering crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def engineering_lead(self) -> Agent:
        return Agent(
            config=self.agents_config['engineering_lead'], # type: ignore[index]
            verbose=True
        )
    @agent
    def core_domain_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['core_domain_engineer'], # type: ignore[index]
            verbose=True
        )
    @agent
    def ui_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['ui_engineer'], # type: ignore[index]
            verbose=True
        )

    @agent
    def test_infra_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['test_infra_engineer'], # type: ignore[index]
            verbose=True
        )

    @task
    def spec_intake_task(self) -> Task:
        return Task(
            config=self.tasks_config['spec_intake'], # type: ignore[index]
            output_pydantic=SpecPack
        )

    @task
    def design_task(self) -> Task:
        return Task(
            config=self.tasks_config['design'], # type: ignore[index]
            output_pydantic=DesignPack
        )

    @task
    def plan_execution_task(self) -> Task:
        return Task(
            config=self.tasks_config['plan_execution'], # type: ignore[index]
            output_pydantic=BuildPlan
        )

    @crew
    def crew(self) -> Crew:
        """Creates the MultiAgentEngineering crew"""

        # CrewAI hierarchical process requires a manager agent that is NOT part of
        # the regular agents list.
        manager = Agent(
            config=self.agents_config['engineering_lead'],  # type: ignore[index]
            verbose=True,
        )

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.hierarchical,
            manager_agent=manager,
            verbose=True,
        )
