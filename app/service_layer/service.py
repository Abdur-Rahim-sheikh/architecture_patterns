from ..domain.models import Batch
from ..domain.models import allocate as model_allocate
from ..adapters.repository import AbstractRepository
from datetime import date


class InvalidSku(Exception):
    pass


def is_valid_sku(sku, batches: list[Batch]):
    return sku in {b.sku for b in batches}


# def allocate(line: OrderLine, repo: AbstractRepository, session) -> str:
#     batches = repo.list()

#     if not is_valid_sku(line.sku, batches):
#         raise InvalidSku(f"Invalid sku {line.sku}")

#     batchref = model_allocate(line, batches)
#     session.commit()
#     return batchref


def allocate(
    orderid: str, sku: str, qty: int, repo: AbstractRepository, session
) -> str:
    batches = repo.list()

    if not is_valid_sku(sku, batches):
        raise InvalidSku(f"Invalid sku {sku}")

    batchref = model_allocate(orderid=orderid, sku=sku, qty=qty, batches=batches)
    session.commit()
    return batchref


def add_batch(
    ref: str, sku: str, qty: int, eta: date | None, repo: AbstractRepository, session
):
    repo.add(Batch(ref, sku, qty, eta))
    session.commit()
