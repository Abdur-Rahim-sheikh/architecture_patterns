from ..domain.events import (
    AllocationRequired,
    BatchCreated,
    OutOfStock,
    BatchQuantityChanged,
)
from ..domain.models import Batch, OrderLine, Product
from .unit_of_work import AbstractUnitOfWork
from ..adapters import email


class InvalidSku(Exception):
    pass


def is_valid_sku(sku, batches: list[Batch]):
    return sku in {b.sku for b in batches}


def allocate(
    event: AllocationRequired,
    uow: AbstractUnitOfWork,
) -> str:
    line = OrderLine(event.orderid, event.sku, event.qty)
    with uow:
        product = uow.products.get(sku=line.sku)
        if product is None:
            raise InvalidSku(f"Invalid sku {line.sku}")
        batchref = product.allocate(line)
        uow.commit()
    return batchref


def add_batch(event: BatchCreated, uow: AbstractUnitOfWork):

    with uow:
        product = uow.products.get(sku=event.sku)
        if product is None:
            product = Product(event.sku, batches=[])
            uow.products.add(product)
        product.batches.append(
            Batch(ref=event.ref, sku=event.sku, qty=event.qty, eta=event.eta)
        )
        uow.commit()


def send_out_of_stock_notification(event: OutOfStock, uow: AbstractUnitOfWork):
    email.send("stock@made.com", f"Out of stock for {event.sku}")


def change_batch_quantity(
    event: BatchQuantityChanged,
    uow: AbstractUnitOfWork,
):
    with uow:
        product = uow.products.get_by_batchref(batchref=event.ref)
        product.change_batch_quantity(ref=event.ref, qty=event.qty)
        uow.commit()
