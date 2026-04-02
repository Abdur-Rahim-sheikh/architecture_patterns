from datetime import date, timedelta

import pytest

from app.domain.models import Batch, OrderLine, OutOfStock, Product


def test_prefers_current_stock_batches_to_shipments():
    in_stock_batch = Batch("in-stock-batch", "RETRO-CLOCK", 100, eta=None)
    shipment_batch = Batch(
        "shipment-batch", "RETRO-CLOCK", 100, eta=date.today() + timedelta(1)
    )
    product = Product("Oref", batches=[in_stock_batch, shipment_batch])
    product.allocate(OrderLine("bula", "RETRO-CLOCK", 10))
    # allocate("oref", "RETRO-CLOCK", 10, [in_stock_batch, shipment_batch])

    assert in_stock_batch.available_quantity == 90
    assert shipment_batch.available_quantity == 100


def test_prefers_earlier_batches():
    earliest = Batch("speedy-batch", "MINIMALIST-SPOON", 100, eta=date.today())
    medium = Batch(
        "normal-batch", "MINIMALIST-SPOON", 100, eta=date.today() + timedelta(1)
    )
    latest = Batch(
        "slow-batch", "MINIMALIST-SPOON", 100, eta=date.today() + timedelta(100)
    )
    product = Product("order1", batches=[medium, earliest, latest])
    product.allocate(OrderLine("aloha", "MINIMALIST-SPOON", 10))
    # allocate("order1", "MINIMALIST-SPOON", 10, [medium, earliest, latest])

    assert earliest.available_quantity == 90
    assert medium.available_quantity == 100
    assert latest.available_quantity == 100


def test_returns_allocated_batch_ref():
    in_stock_batch = Batch("in-stock-batch-ref", "HIGHBROW-POSTER", 100, eta=None)
    shipment_batch = Batch(
        "shipment-batch-ref", "HIGHBROW-POSTER", 100, eta=date.today() + timedelta(1)
    )
    product = Product("order1", batches=[in_stock_batch, shipment_batch])
    allocation = product.allocate(OrderLine("aloha", "HIGHBROW-POSTER", 10))

    assert allocation == in_stock_batch.reference


def test_raises_out_of_stock_exception_if_cannot_allocate():
    batch = Batch("batch1", "SMALL-FORK", 10, eta=date.today())
    product = Product("order1", batches=[batch])
    product.allocate(OrderLine("aloha", "SMALL-FORK", 10))

    with pytest.raises(OutOfStock, match="SMALL-FORK"):
        ref = product.allocate(OrderLine("order2", "SMALL-FORK", 1))
        print(ref, batch.available_quantity)
