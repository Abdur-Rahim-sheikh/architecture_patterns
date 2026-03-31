from datetime import date

from ..domain.models import Batch
from ..domain.models import allocate as model_allocate
from .unit_of_work import AbstractUnitOfWork


class InvalidSku(Exception):
    pass


def is_valid_sku(sku, batches: list[Batch]):
    return sku in {b.sku for b in batches}


# def allocate(
#     orderid: str, sku: str, qty: int, repo: AbstractRepository, session
# ) -> str:
#     batches = repo.list()

#     if not is_valid_sku(sku, batches):
#         raise InvalidSku(f"Invalid sku {sku}")


#     batchref = model_allocate(orderid=orderid, sku=sku, qty=qty, batches=batches)
#     session.commit()
#     return batchref
def allocate(orderid: str, sku: str, qty: int, uow: AbstractUnitOfWork) -> str:
    with uow:
        batches = uow.batches.list()

        if not is_valid_sku(sku, batches):
            raise InvalidSku(f"Invalid sku {sku}")

        batchref = model_allocate(orderid=orderid, sku=sku, qty=qty, batches=batches)
        uow.commit()
        return batchref


def add_batch(ref: str, sku: str, qty: int, eta: date | None, uow: AbstractUnitOfWork):

    with uow:
        uow.batches.add(Batch(ref, sku, qty, eta))
        uow.commit()
