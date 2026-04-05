from datetime import date

from app.domain.events import AllocationRequired, BatchCreated, BatchQuantityChanged
from app.service_layer import messagebus

from ..fakes import FakeUnitOfWork, FakeUnitOfWorkWithFakeMessageBus


class TestChangeBatchQuantity:
    def test_changes_available_quantity(self):
        uow = FakeUnitOfWork()
        messagebus.handle(BatchCreated("batch1", "ADORABLE-SETTEE", 100, None), uow)
        [batch] = uow.products.get(sku="ADORABLE-SETTEE").batches
        assert batch.available_quantity == 100  # (1)

        messagebus.handle(BatchQuantityChanged("batch1", 50), uow)

        assert batch.available_quantity == 50  # (1)

    def test_reallocates_if_necessary(self):
        uow = FakeUnitOfWork()
        event_history = [
            BatchCreated("batch1", "INDIFFERENT-TABLE", 50, None),
            BatchCreated("batch2", "INDIFFERENT-TABLE", 50, date.today()),
            AllocationRequired("order1", "INDIFFERENT-TABLE", 20),
            AllocationRequired("order2", "INDIFFERENT-TABLE", 20),
        ]
        for e in event_history:
            messagebus.handle(e, uow)
        [batch1, batch2] = uow.products.get(sku="INDIFFERENT-TABLE").batches
        assert batch1.available_quantity == 10
        assert batch2.available_quantity == 50

        messagebus.handle(BatchQuantityChanged("batch1", 25), uow)

        # order1 or order2 will be deallocated, so we'll have 25 - 20
        assert batch1.available_quantity == 5  # (2)
        # and 20 will be reallocated to the next batch
        assert batch2.available_quantity == 30  # (2)

    def test_reallocates_if_necessary_isolated():
        uow = FakeUnitOfWorkWithFakeMessageBus()

        # test setup as before
        event_history = [
            BatchCreated("batch1", "INDIFFERENT-TABLE", 50, None),
            BatchCreated("batch2", "INDIFFERENT-TABLE", 50, date.today()),
            AllocationRequired("order1", "INDIFFERENT-TABLE", 20),
            AllocationRequired("order2", "INDIFFERENT-TABLE", 20),
        ]
        for e in event_history:
            messagebus.handle(e, uow)
        [batch1, batch2] = uow.products.get(sku="INDIFFERENT-TABLE").batches
        assert batch1.available_quantity == 10
        assert batch2.available_quantity == 50

        messagebus.handle(BatchQuantityChanged("batch1", 25), uow)

        # assert on new events emitted rather than downstream side-effects
        [reallocation_event] = uow.events_published
        assert isinstance(reallocation_event, AllocationRequired)
        assert reallocation_event.orderid in {"order1", "order2"}
        assert reallocation_event.sku == "INDIFFERENT-TABLE"
