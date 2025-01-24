import asyncio

from sagent import BasicAgent
from sagent.orchestrator import Orchestrator


class LocalhostRequestAgent(BasicAgent):
    async def perform(self) -> None:
        await self.http("http://localhost", "GET")


orchestrator = Orchestrator()
orchestrator.register_agent(LocalhostRequestAgent, task_instances=1)
asyncio.run(orchestrator.begin())
