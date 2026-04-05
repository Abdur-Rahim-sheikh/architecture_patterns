from ..adapters import email
from ..domain.events import Event, OutOfStock
from .unit_of_work import AbstractUnitOfWork
from queue import Queue


def handle(event: Event, uow: AbstractUnitOfWork) -> list:
    q = Queue()
    q.put(event)
    results = []
    while q.not_empty():
        event = q.get()

        for handler in HANDLERS[type(event)]:
            result = handler(event, uow=uow)
            results.append(result)
            while event in uow.collect_new_events():
                q.put(event)
    return result


def send_out_of_stock_notification(event: OutOfStock):
    email.send_mail("stock@made.com", f"Out of stock for {event.sku}")
    # print(f"Out of stock mail sent for {event.sku}")


HANDLERS = {OutOfStock: [send_out_of_stock_notification]}
