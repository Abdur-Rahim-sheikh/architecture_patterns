import pytest

from ..repository import FakeRepository
from ..service import InvalidSku, add_batch, allocate


class FakeSession:
    committed = False

    def commit(self):
        self.committed = True


def test_returns_allocation():
    # line = OrderLine("o1", "COMPLICATED-LAMP", 10)

    repo = FakeRepository.for_batch("b1", "COMPLICATED-LAMP", 100, eta=None)

    result = allocate("o1", "COMPLICATED-LAMP", 10, repo, FakeSession())
    assert result == "b1"


def test_allocate_returns_allocation():
    repo, session = FakeRepository([]), FakeSession()
    add_batch("batch1", "COMPLICATED-LAMP", 100, None, repo, session)
    result = allocate("o1", "COMPLICATED-LAMP", 10, repo, session)
    assert result == "batch1"


def test_allocate_errors_for_invalid_sku():
    repo, session = FakeRepository([]), FakeSession()
    add_batch("b1", "AREALSKU", 100, None, repo, session)

    with pytest.raises(InvalidSku, match="Invalid sku NONEXISTENTSKU"):
        allocate("o1", "NONEXISTENTSKU", 10, repo, FakeSession())


def test_add_batch():
    repo, session = FakeRepository([]), FakeSession()
    add_batch("b1", "CRUNCHY_ARMCHAIR", 100, None, repo, session)
    assert repo.get("b1") is not None
    assert session.committed
