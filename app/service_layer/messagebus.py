from queue import Queue

from ..domain.events import (
    AllocationRequired,
    BatchCreated,
    BatchQuantityChanged,
    Event,
    OutOfStock,
)
from . import handlers
from .unit_of_work import AbstractUnitOfWork


def handle(event: Event, uow: AbstractUnitOfWork) -> list:
    q = Queue()
    q.put(event)
    results = []

    while not q.empty():
        event = q.get()

        for handler in HANDLERS[type(event)]:
            result = handler(event, uow=uow)
            results.append(result)
            for new_event in uow.collect_new_events():
                q.put(new_event)

    return results


HANDLERS = {
    OutOfStock: [handlers.send_out_of_stock_notification],
    BatchCreated: [handlers.add_batch],
    BatchQuantityChanged: [handlers.change_batch_quantity],
    AllocationRequired: [handlers.allocate],
}
