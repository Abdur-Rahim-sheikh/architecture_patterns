from app.service_layer.unit_of_work import AbstractUnitOfWork
from app.adapters import AbstractRepository, AbstractNotifications
from app.domain.events import Event
from collections import defaultdict


class FakeNotifications(AbstractNotifications):
    def __init__(self):
        self.sent: dict[str, list[str]] = defaultdict(list)

    def send(self, destination, message):
        self.sent[destination].append(message)


class FakeUnitOfWork(AbstractUnitOfWork):
    def __init__(self):
        self.products = FakeRepository([])
        self.committed = False

    def _commit(self):
        self.committed = True

    def rollback(self):
        pass


class FakeUnitOfWorkWithFakeMessageBus(FakeUnitOfWork):
    def __init__(self):
        super().__init__()
        self.events_published: list[Event] = []

    def collect_new_events(self):
        self.events_published += super().collect_new_events()
        return []


class FakeRepository(AbstractRepository):
    def __init__(self, products):
        super().__init__()
        self._products = set(products)

    def _add(self, batch):
        self._products.add(batch)

    def _get(self, sku):
        return next((b for b in self._products if b.sku == sku), None)

    def _get_by_batchref(self, batchref):
        return next(
            (p for p in self._products for b in p.batches if b.reference == batchref),
            None,
        )


class FakeSession:
    committed = False

    def commit(self):
        self.committed = True
