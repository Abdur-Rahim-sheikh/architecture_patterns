from app.service_layer import SqlAlchemyUnitOfWork, messagebus
from app.domain import commands
from app import views
from datetime import date
import pytest

# check the README.md for this fixture


@pytest.mark.usefixtures("clean_redis")
def test_allocations_view(sqlite_session_factory):
    uow = SqlAlchemyUnitOfWork(sqlite_session_factory)
    messagebus.handle(commands.CreateBatch("sku1batch", "sku1", 50, None), uow)  # (1)
    messagebus.handle(commands.CreateBatch("sku2batch", "sku2", 50, date.today()), uow)
    messagebus.handle(commands.Allocate("order1", "sku1", 20), uow)
    messagebus.handle(commands.Allocate("order1", "sku2", 20), uow)
    # add a spurious batch and order to make sure we're getting the right ones
    messagebus.handle(
        commands.CreateBatch("sku1batch-later", "sku1", 50, date.today()), uow
    )
    messagebus.handle(commands.Allocate("otherorder", "sku1", 30), uow)
    messagebus.handle(commands.Allocate("otherorder", "sku2", 10), uow)

    # assert views.allocations("order1", uow) == [
    #     {"sku": "sku1", "batchref": "sku1batch"},
    #     {"sku": "sku2", "batchref": "sku2batch"},
    # ]
    print(f"{views.allocations("order1")=}")
    assert views.allocations("order1") == [
        {"sku": "sku1", "batchref": "sku1batch"},
        {"sku": "sku2", "batchref": "sku2batch"},
    ]


@pytest.mark.usefixtures("clean_redis")
def test_deallocation(sqlite_session_factory):
    uow = SqlAlchemyUnitOfWork(sqlite_session_factory)
    messagebus.handle(commands.CreateBatch("b1", "sku1", 50, None), uow)
    messagebus.handle(commands.CreateBatch("b2", "sku1", 50, date.today()), uow)
    messagebus.handle(commands.Allocate("o1", "sku1", 40), uow)
    messagebus.handle(commands.ChangeBatchQuantity("b1", 10), uow)

    assert views.allocations("o1") == [
        {"sku": "sku1", "batchref": "b2"},
    ]
