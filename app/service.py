from .models import Batch, OrderLine
from .models import allocate as model_allocate
from .repository import AbstractRepository


class InvalidSku(Exception):
    pass


def is_valid_sku(sku, batches: list[Batch]):
    return sku in {b.sku for b in batches}


def allocate(line: OrderLine, repo: AbstractRepository, session) -> str:
    batches = repo.list()

    if not is_valid_sku(line.sku, batches):
        raise InvalidSku(f"Invalid sku {line.sku}")

    batchref = model_allocate(line, batches)
    session.commit()
    return batchref
