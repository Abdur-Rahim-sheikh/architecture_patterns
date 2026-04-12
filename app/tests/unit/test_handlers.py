from datetime import date

import pytest

from app import bootstrap
from app.domain.commands import Allocate, ChangeBatchQuantity, CreateBatch
from app.service_layer.handlers import InvalidSku

from ..fakes import FakeNotifications, FakeUnitOfWork


def bootstrap_test_app():
    return bootstrap.bootstrap(
        start_orm=False,
        uow=FakeUnitOfWork(),
        notifications=lambda *args: None,
        publish=lambda *args: None,
    )


class TestAddBatch:
    def test_for_new_product(self):
        bus = bootstrap_test_app()

        bus.handle(CreateBatch("b1", "CRUNCHY-ARMCHAIR", 100, None))
        assert bus.uow.products.get("CRUNCHY-ARMCHAIR") is not None
        assert bus.uow.committed

    def test_for_existing_product(self):
        bus = bootstrap_test_app()
        bus.handle(CreateBatch("b1", "GARISH-RUG", 100, None))
        bus.handle(CreateBatch("b2", "GARISH-RUG", 99, None))
        assert "b2" in [b.reference for b in bus.uow.products.get("GARISH-RUG").batches]


class TestAllocate:
    def test_returns_allocation(self):
        bus = bootstrap_test_app()
        bus.handle(CreateBatch("batch1", "COMPLICATED-LAMP", 100, None))
        results = bus.handle(Allocate("o1", "COMPLICATED-LAMP", 10))
        assert results.pop(0) == "batch1"

    def test_errors_for_invalid_sku(self):
        bus = bootstrap_test_app()
        bus.handle(CreateBatch("b1", "AREALSKU", 100, None))

        with pytest.raises(InvalidSku, match="Invalid sku NONEXISTENTSKU"):
            bus.handle(Allocate("o1", "NONEXISTENTSKU", 10))

    def test_commits(self):
        bus = bootstrap_test_app()
        bus.handle(CreateBatch("b1", "OMINOUS-MIRROR", 100, None))
        bus.handle(Allocate("o1", "OMINOUS-MIRROR", 10))
        assert bus.uow.committed

    def test_sends_email_on_out_of_stock_error(self):
        fake_notifs = FakeNotifications()
        bus = bootstrap.bootstrap(
            start_orm=False,
            uow=FakeUnitOfWork(),
            notifications=fake_notifs,
            publish=lambda *args: None,
        )
        bus.handle(CreateBatch("b1", "POPULAR-CURTAINS", 9, None))

        bus.handle(Allocate("o1", "POPULAR-CURTAINS", 10))
        assert fake_notifs.sent["stock@made.com"] == [
            "Out of stock for POPULAR-CURTAINS",
        ]


class TestChangeBatchQuantity:
    def test_changes_available_quantity(self):
        bus = bootstrap_test_app()
        bus.handle(CreateBatch("batch1", "ADORABLE-SETTEE", 100, None))
        [batch] = bus.uow.products.get(sku="ADORABLE-SETTEE").batches
        assert batch.available_quantity == 100

        bus.handle(ChangeBatchQuantity("batch1", 50))

        assert batch.available_quantity == 50

    def test_reallocates_if_necessary(self):
        bus = bootstrap_test_app()
        event_history = [
            CreateBatch("batch1", "INDIFFERENT-TABLE", 50, None),
            CreateBatch("batch2", "INDIFFERENT-TABLE", 50, date.today()),
            Allocate("order1", "INDIFFERENT-TABLE", 20),
            Allocate("order2", "INDIFFERENT-TABLE", 20),
        ]
        for e in event_history:
            bus.handle(e)
        [batch1, batch2] = bus.uow.products.get(sku="INDIFFERENT-TABLE").batches
        assert batch1.available_quantity == 10
        assert batch2.available_quantity == 50

        bus.handle(ChangeBatchQuantity("batch1", 25))

        # order1 or order2 will be deallocated, so we'll have 25 - 20
        assert batch1.available_quantity == 5
        # and 20 will be reallocated to the next batch
        assert batch2.available_quantity == 30
