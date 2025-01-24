from asyncio import Task, create_task, sleep, wait
from asyncio.exceptions import CancelledError
from dataclasses import dataclass
from typing import Any

from .agent import AbstractAgent, BasicAgent
from .executor import AsyncExecutor


@dataclass
class _ExecutedAgent:
    agent: AbstractAgent
    agent_cls: type[AbstractAgent]
    task_instances: int


class Orchestrator:
    _executor: AsyncExecutor
    _agents_cls: list[tuple[type[AbstractAgent], int]]
    _agent_awaited_tasks: set[Task[Any]]

    _executed_agents: list[_ExecutedAgent]

    def __init__(self) -> None:
        self._executor = AsyncExecutor()

        self._agents_cls = []
        self._agent_awaited_tasks = set()
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
                # Push task to background store with task clearing
                task = self._executor.agent_executor_task(executed_agent.agent)
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

        try:
            await wait(self._agent_awaited_tasks)
        except CancelledError:
            print("Orchestrator task has been cancelled.")
            return

    async def orchestrator_task(self) -> None:
        prev_requests_done = 0
        while True:
            print("Perform total calls:", self._executor.stat_perform_calls)
            requests_done = sum(
                [
                    e_agent.agent.stat_http_requests_done
                    for e_agent in self._executed_agents
                    if isinstance(e_agent.agent, BasicAgent)
                ]
            )
            print("Total HTTP requests: ", requests_done)
            new_requests = requests_done - prev_requests_done
            print("Done HTTP requests", new_requests)
            prev_requests_done = requests_done
            print("-" * 30)
            await sleep(1)
