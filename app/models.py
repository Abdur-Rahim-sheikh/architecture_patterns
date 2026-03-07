from datetime import date
from dataclasses import dataclass


class OutOfStock(Exception):
    pass


@dataclass(unsafe_hash=True)
class OrderLine:
    orderid: str
    sku: str
    qty: int


class Batch:
    def __init__(self, ref: str, sku: str, qty: int, eta: date | None = None):
        self.reference = ref
        self.sku = sku
        self.eta = eta
        self._purchased_quantity = qty
        self._allocated = set()
        self._total_allocated = 0

    def __gt__(self, other: "Batch"):
        if self.eta is None:
            return False
        if other.eta is None:
            return True
        return self.eta > other.eta

    def can_allocate(self, line: OrderLine) -> bool:
        return self.sku == line.sku and self.available_quantity >= line.qty

    def allocate(self, line: OrderLine):
        if self.can_allocate(line):
            self._allocated.add(line)
            self._total_allocated += line.qty

    def deallocate(self, line: OrderLine):
        if line in self._allocated:
            self._allocated.remove(line)
            self._total_allocated -= line.qty

    @property
    def allocated_quantity(self) -> int:
        return self._total_allocated

    @property
    def available_quantity(self) -> int:
        return self._purchased_quantity - self._total_allocated


def allocate(line: OrderLine, batches: list[Batch]) -> str:
    try:
        batch = next(b for b in sorted(batches) if b.can_allocate(line))
    except StopIteration:
        raise OutOfStock(f"Out of stock for sku {line.sku}")
    batch.allocate(line)
    return batch.reference
