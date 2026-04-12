import logging
from queue import Queue
from typing import Callable, Type

from ..domain.commands import Command
from ..domain.events import Event
from .unit_of_work import AbstractUnitOfWork

logger = logging.getLogger(__name__)

logger.setLevel(logging.DEBUG)
Message = Command | Event


class MessageBus:
    def __init__(
        self,
        uow: AbstractUnitOfWork,
        event_handlers: dict[Type[Event], list[Callable]],
        command_handlers: dict[Type[Command], Callable],
    ):
        self.uow = uow
        self.event_handlers = event_handlers
        self.command_handlers = command_handlers
        # print(f"{self.uow=}, {self.event_handlers=}, {self.command_handlers=}")

    def handle(self, message: Message) -> list:
        q = Queue()
        q.put(message)
        results = []

        while not q.empty():
            message = q.get()

            if isinstance(message, Event):
                self.handle_event(message, q)
            elif isinstance(message, Command):
                result = self.handle_command(message, q)
                results.append(result)

            else:
                raise Exception(f"{message} was not an Event or Command")

        return results

    def handle_event(self, event: Event, queue: Queue[Message]):
        for handler in self.event_handlers[type(event)]:
            logger.debug(f"{queue.queue=}, {handler=}, {isinstance(event, Event)=}")

            try:
                handler(event)

                for new_event in self.uow.collect_new_events():
                    queue.put(new_event)

            except Exception:
                logger.exception("Failed to handle event!")
                continue

    def handle_command(self, command: Command, queue: Queue[Message]):

        try:
            handler = self.command_handlers[type(command)]
            result = handler(command)
            for new_event in self.uow.collect_new_events():
                queue.put(new_event)

            return result
        except Exception:
            logger.exception("Exception handling command %s", command)
            raise
