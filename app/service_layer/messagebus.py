import logging
from queue import Queue


from ..domain.commands import Allocate, ChangeBatchQuantity, Command, CreateBatch
from ..domain.events import Allocated, Event, OutOfStock, Deallocated
from . import handlers
from .unit_of_work import AbstractUnitOfWork

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
        logger.debug(f"{queue.queue=}, {handler=}, {isinstance(event, Event)=}")

        try:
            handler(event, uow=uow)

            for new_event in uow.collect_new_events():
                queue.put(new_event)

        except Exception:
            logger.exception("Failed to handle event!")
            continue


def handle_command(
    command: Command,
    queue: Queue[Message],
    uow: AbstractUnitOfWork,
):

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
    Allocated: [
        handlers.publish_allocated_event,
        handlers.add_allocation_to_read_model,
    ],
    Deallocated: [handlers.remove_allocation_from_read_model, handlers.reallocate],
}
COMMAND_HANDLERS = {
    CreateBatch: handlers.add_batch,
    ChangeBatchQuantity: handlers.change_batch_quantity,
    Allocate: handlers.allocate,
}
