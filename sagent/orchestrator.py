from asyncio import Task, create_task, sleep, wait
from dataclasses import dataclass
from typing import Any

from .agent import AbstractAgent


@dataclass
class _ExecutedAgent:
    agent: AbstractAgent
    agent_cls: type[AbstractAgent]
    task_instances: int


class Orchestrator:
    _agents_cls: list[tuple[type[AbstractAgent], int]]
    _agent_awaited_tasks: set[Task[Any]]
    _perform_counter: int
    _executed_agents: list[_ExecutedAgent]

    def __init__(self) -> None:
        self._agents_cls = []
        self._agent_awaited_tasks = set()
        self._perform_counter = 0
        self._executed_agents = []

    def register_agent(
        self, agent_cls: type[AbstractAgent], task_instances: int = 1
    ) -> None:
        if self._agent_awaited_tasks:
            raise Exception("Tried to register agent while already started")
        self._agents_cls.append((agent_cls, task_instances))

    async def begin(self):
        await self.prepare_execution_agents()
        await self.construct_agent_tasks()
        await self.blocking_wait_for_agent_perform_tasks()

    async def prepare_execution_agents(self):
        for agent_cls, agent_task_instances in self._agents_cls:
            agent = agent_cls()

            self._executed_agents.append(
                _ExecutedAgent(
                    agent=agent,
                    agent_cls=agent_cls,
                    task_instances=agent_task_instances,
                )
            )

    async def construct_agent_tasks(self) -> None:
        if self._agent_awaited_tasks:
            raise Exception(
                "Tried to construct agent tasks while it already constructed/executed"
            )

        for executed_agent in self._executed_agents:
            for _ in range(executed_agent.task_instances):
                coro = self.agent_perform_task(executed_agent.agent)
                task = create_task(coro)

                # Push task to background store with task clearing
                self._agent_awaited_tasks.add(task)
                task.add_done_callback(self._agent_awaited_tasks.discard)

        coro = self.orchestrator_task()
        task = create_task(coro)

        # Push task to background store with task clearing
        self._agent_awaited_tasks.add(task)
        task.add_done_callback(self._agent_awaited_tasks.discard)

    async def blocking_wait_for_agent_perform_tasks(self):
        # We just lock (wait) for all agent tasks is completed.
        # Which is never should happen unless exception is propagated.

        await wait(self._agent_awaited_tasks)

    async def orchestrator_task(self) -> None:
        prev_requests_done = 0
        while True:
            print("Perform total calls:", self._perform_counter)
            requests_done = sum(
                [e_agent.agent.http_requests_done for e_agent in self._executed_agents]
            )
            print("Total HTTP requests: ", requests_done)
            new_requests = requests_done - prev_requests_done
            print("Done HTTP requests", new_requests)
            prev_requests_done = requests_done
            print("-" * 30)
            await sleep(1)

    async def agent_perform_task(self, agent: AbstractAgent):
        """Task for async execution of each agent."""
        try:
            await agent.bootstrap()
        except Exception as e:
            print(e)
        await sleep(0)

        while True:
            # We release flow to agent so it can do action defined in him
            try:
                await agent.perform()
            except Exception as e:
                print(e)
            # We may not assume that agent will yield execution flow to next agent
            # so we should yield execution to next one
            await sleep(0)
            self._perform_counter += 1
