from asyncio import Task, create_task, sleep
from logging import Logger, getLogger

from .agent import AbstractAgent


class AsyncExecutor:
    logger: Logger
    stat_perform_calls: int

    def __init__(self) -> None:
        self.logger = getLogger("sagent.executor")
        self.stat_perform_calls = 0

    def agent_executor_task(self, agent: AbstractAgent) -> Task[None]:
        """Create async task for execution of agent given."""
        coro = self._agent_execute(agent)
        task = create_task(coro)
        return task

    async def _agent_execute(self, agent: AbstractAgent) -> None:
        """Task for async execution of agent given.

        Bootstrap agent and then perform actions in loop.
        """

        try:
            await agent.bootstrap()
        except Exception as e:
            self.logger.error(
                f"Agent {agent} failed to bootstrap. Agent has been aborted from execution",
                exc_info=e,
            )
            return

        # We should yield execution to next agent bootstrap.
        await sleep(0)

        while True:
            # We release flow to agent so it can do action defined in him
            try:
                await agent.perform()

                # We may not assume that agent will yield execution flow to next agent
                # so we should yield execution to next one
                await sleep(0)
            except Exception as e:
                self.logger.error(
                    f"Agent {agent} failed to perform. Agent has been aborted from execution",
                    exc_info=e,
                )
                return
            self.stat_perform_calls += 1
