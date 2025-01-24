"""Agent module implementation.

Agent - is something like worker with described actions that will be performed in parallel
(single agent orchestration within multiple tasks (workers) or within multiple agents).
"""

from abc import ABCMeta, abstractmethod

from .agent_http_mixin import AgentHTTPMixin


class AbstractAgent(metaclass=ABCMeta):
    """Abstracted agent useful for using custom mixins without default ones.

    You can use that class but it's recommended to use `BasicAgent` instead or create own subclass.
    """

    def __init__(self) -> None:
        pass

    async def bootstrap(self) -> None:
        """Method that is called when agent is created and should be bootstrapped.

        Override to perform actions you need to be ran only once and before performing actions.
        """

    @abstractmethod
    async def perform(self) -> None:
        """Method that is called when agent should perform actions.

        Override to perform actions you need to be ran every times this agent performs.
        """


class BasicAgent(AgentHTTPMixin, AbstractAgent):
    """Basic agent with HTTP capabilities that should be used by default."""
