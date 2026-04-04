from ..adapters import email
from ..domain.events import Event, OutOfStock


def handle(event: Event):
    for handler in HANDLERS[type(event)]:
        handler(event)


def send_out_of_stock_notification(event: OutOfStock):
    email.send_mail("stock@made.com", f"Out of stock for {event.sku}")
    # print(f"Out of stock mail sent for {event.sku}")


HANDLERS = {OutOfStock: [send_out_of_stock_notification]}
