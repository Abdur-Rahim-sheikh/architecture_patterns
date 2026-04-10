from ..domain.events import OutOfStock, Allocated, Deallocated
from ..domain.commands import Allocate, CreateBatch, ChangeBatchQuantity
from ..domain.models import Batch, OrderLine, Product
from .unit_of_work import AbstractUnitOfWork
from ..adapters import email
from ..adapters import redis_eventpublisher


class InvalidSku(Exception):
    pass


def is_valid_sku(sku, batches: list[Batch]):
    return sku in {b.sku for b in batches}


def allocate(
    message: Allocate,
    uow: AbstractUnitOfWork,
) -> str:
    line = OrderLine(message.orderid, message.sku, message.qty)
    with uow:
        product = uow.products.get(sku=line.sku)
        if product is None:
            raise InvalidSku(f"Invalid sku {line.sku}")
        batchref = product.allocate(line)
        uow.commit()
    return batchref


def reallocate(event: Deallocated, uow: AbstractUnitOfWork):
    with uow:
        product = uow.products.get(sku=event.sku)

        product.events.append(
            Allocate(orderid=event.orderid, sku=event.sku, qty=event.sku)
        )


def add_batch(message: CreateBatch, uow: AbstractUnitOfWork):

    with uow:
        product = uow.products.get(sku=message.sku)
        if product is None:
            product = Product(message.sku, batches=[])
            uow.products.add(product)
        product.batches.append(
            Batch(ref=message.ref, sku=message.sku, qty=message.qty, eta=message.eta)
        )
        uow.commit()


def send_out_of_stock_notification(event: OutOfStock, uow: AbstractUnitOfWork):
    email.send("stock@made.com", f"Out of stock for {event.sku}")


def change_batch_quantity(
    message: ChangeBatchQuantity,
    uow: AbstractUnitOfWork,
):
    with uow:
        product = uow.products.get_by_batchref(batchref=message.ref)
        product.change_batch_quantity(ref=message.ref, qty=message.qty)
        uow.commit()


def add_allocation_to_read_model(event: Allocated, uow: AbstractUnitOfWork):
    redis_eventpublisher.update_readmodel(event.orderid, event.sku, event.batchref)


def remove_allocation_from_read_model(event: Allocated, uow: AbstractUnitOfWork):
    redis_eventpublisher.update_readmodel(event.orderid, event.sku, event.batchref)


def publish_allocated_event(event: Allocated, uow: AbstractUnitOfWork):
    redis_eventpublisher.publish("line_allocated", event)
