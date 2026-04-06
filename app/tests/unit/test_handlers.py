from datetime import date
from unittest import mock

import pytest

from app.domain.events import AllocationRequired, BatchCreated, BatchQuantityChanged
from app.service_layer import messagebus
from app.service_layer.handlers import InvalidSku

from ..fakes import FakeUnitOfWork


class TestAddBatch:
    def test_for_new_product(self):
        uow = FakeUnitOfWork()
        messagebus.handle(BatchCreated("b1", "CRUNCHY-ARMCHAIR", 100, None), uow)
        assert uow.products.get("CRUNCHY-ARMCHAIR") is not None
        assert uow.committed

    def test_for_existing_product(self):
        uow = FakeUnitOfWork()
        messagebus.handle(BatchCreated("b1", "GARISH-RUG", 100, None), uow)
        messagebus.handle(BatchCreated("b2", "GARISH-RUG", 99, None), uow)
        assert "b2" in [b.reference for b in uow.products.get("GARISH-RUG").batches]


class TestAllocate:
    def test_returns_allocation(self):
        uow = FakeUnitOfWork()
        messagebus.handle(BatchCreated("batch1", "COMPLICATED-LAMP", 100, None), uow)
        results = messagebus.handle(
            AllocationRequired("o1", "COMPLICATED-LAMP", 10), uow
        )
        assert results.pop(0) == "batch1"

    def test_errors_for_invalid_sku(self):
        uow = FakeUnitOfWork()
        messagebus.handle(BatchCreated("b1", "AREALSKU", 100, None), uow)

        with pytest.raises(InvalidSku, match="Invalid sku NONEXISTENTSKU"):
            messagebus.handle(AllocationRequired("o1", "NONEXISTENTSKU", 10), uow)

    def test_commits(self):
        uow = FakeUnitOfWork()
        messagebus.handle(BatchCreated("b1", "OMINOUS-MIRROR", 100, None), uow)
        messagebus.handle(AllocationRequired("o1", "OMINOUS-MIRROR", 10), uow)
        assert uow.committed

    def test_sends_email_on_out_of_stock_error(self):
        uow = FakeUnitOfWork()
        messagebus.handle(BatchCreated("b1", "POPULAR-CURTAINS", 9, None), uow)

        with mock.patch("app.adapters.email.send") as mock_send_mail:
            messagebus.handle(AllocationRequired("o1", "POPULAR-CURTAINS", 10), uow)
            assert mock_send_mail.call_args == mock.call(
                "stock@made.com", "Out of stock for POPULAR-CURTAINS"
            )


class TestChangeBatchQuantity:
    def test_changes_available_quantity(self):
        uow = FakeUnitOfWork()
        messagebus.handle(BatchCreated("batch1", "ADORABLE-SETTEE", 100, None), uow)
        [batch] = uow.products.get(sku="ADORABLE-SETTEE").batches
        assert batch.available_quantity == 100

        messagebus.handle(BatchQuantityChanged("batch1", 50), uow)

        assert batch.available_quantity == 50

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
        assert batch1.available_quantity == 5
        # and 20 will be reallocated to the next batch
        assert batch2.available_quantity == 30
