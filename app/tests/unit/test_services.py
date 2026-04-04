from unittest import mock

import pytest

from app.adapters.repository import AbstractRepository
from app.service_layer.service import InvalidSku, add_batch, allocate
from app.service_layer.unit_of_work import AbstractUnitOfWork


class FakeUnitOfWork(AbstractUnitOfWork):
    def __init__(self):
        self.products = FakeRepository([])
        self.committed = False

    def _commit(self):
        self.committed = True

    def rollback(self):
        pass


class FakeRepository(AbstractRepository):
    def __init__(self, products):
        super().__init__()
        self._products = set(products)

    def _add(self, batch):
        self._products.add(batch)

    def _get(self, sku):
        return next((b for b in self._products if b.sku == sku), None)


class FakeSession:
    committed = False

    def commit(self):
        self.committed = True


def test_add_batch():
    uow = FakeUnitOfWork()
    add_batch("b1", "CRUNCHY-ARMCHAIR", 100, None, uow)
    assert uow.products.get("CRUNCHY-ARMCHAIR") is not None, uow.products
    assert uow.committed


def test_allocate_returns_allocation():
    uow = FakeUnitOfWork()
    add_batch("batch1", "COMPLICATED-LAMP", 100, None, uow)
    result = allocate("o1", "COMPLICATED-LAMP", 10, uow)
    assert result == "batch1"


def test_allocate_errors_for_invalid_sku():
    uow = FakeUnitOfWork()
    add_batch("b1", "AREALSKU", 100, None, uow)

    with pytest.raises(InvalidSku, match="Invalid sku NONEXISTENTSKU"):
        allocate("o1", "NONEXISTENTSKU", 10, uow)


def test_commits():
    uow = FakeUnitOfWork()
    add_batch("b1", "OMINOUS-MIRROR", 100, None, uow)
    allocate("o1", "OMINOUS-MIRROR", 10, uow)
    assert uow.committed is True


def test_sends_email_on_out_of_stock_error():
    uow = FakeUnitOfWork()
    add_batch("b1", "POPULAR-CURTAINS", 9, None, uow)

    with mock.patch("app.adapters.email.send_mail") as mock_send_mail:
        allocate("o1", "POPULAR-CURTAINS", 10, uow)
        assert mock_send_mail.call_args == mock.call(
            "stock@made.com",
            "Out of stock for POPULAR-CURTAINS",
        )
