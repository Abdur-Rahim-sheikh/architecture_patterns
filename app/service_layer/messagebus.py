import logging
from queue import Queue

from ..domain.commands import Allocate, ChangeBatchQuantity, Command, CreateBatch
from ..domain.events import (
    Event,
    OutOfStock,
)
from . import handlers
from .unit_of_work import AbstractUnitOfWork
from tenacity import Retrying, RetryError, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
Message = Command | Event


def handle(message: Message, uow: AbstractUnitOfWork) -> list:
    q = Queue()
    q.put(message)
    results = []

    while not q.empty():
        message = q.get()
        if isinstance(message, Event):
            handle_event(message, q, uow)
        elif isinstance(message, Command):
            result = handle_command(message, q, uow)
            results.append(result)

        else:
            raise Exception(f"{message} was not an Event or Command")

    return results


def handle_event(event: Event, queue: Queue[Message], uow: AbstractUnitOfWork):
    for handler in EVENT_HANDLERS[type(event)]:
        try:
            for attepmt in Retrying(
                stop=stop_after_attempt(3), wait=wait_exponential()
            ):
                with attepmt:
                    handler(event, uow=uow)

                    for new_event in uow.collect_new_events():
                        queue.put(new_event)
        except RetryError as retry_failure:
            n = retry_failure.last_attempt.attempt_number
            logger.error(f"Failed to handle event {n} times, giving up!")
            continue


def handle_command(
    command: Command,
    queue: Queue[Message],
    uow: AbstractUnitOfWork,
):
    logger.debug("handling command %s", command)
    try:
        handler = COMMAND_HANDLERS[type(command)]
        result = handler(command, uow=uow)
        for new_event in uow.collect_new_events():
            queue.put(new_event)

        return result
    except Exception:
        logger.exception("Exception handling command %s", command)
        raise


EVENT_HANDLERS = {
    OutOfStock: [handlers.send_out_of_stock_notification],
}
COMMAND_HANDLERS = {
    CreateBatch: handlers.add_batch,
    ChangeBatchQuantity: handlers.change_batch_quantity,
    Allocate: handlers.allocate,
}
