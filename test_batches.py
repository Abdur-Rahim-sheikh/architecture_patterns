from models import Batch, OrderLine
from datetime import date


def test_allocation_to_a_batch_reduces_the_available_quantity():
    batch = Batch("batch-001", "SMALL-TABLE", qty=20, eta=date.today())
    line = OrderLine("order-ref", "SMALL-TABLE", 2)
    batch.allocate(line)
    assert batch._purchased_quantity == 18


def make_batch_and_line(sku, batch_qty, line_qty):
    return (
        Batch("batch-001", sku, batch_qty, date.today()),
        OrderLine("order-123", sku, line_qty),
    )


def test_can_allocate_if_available_greater_than_required():
    large_batch, small_line = make_batch_and_line("E", 20, 2)
    assert large_batch.can_allocate(small_line)


def test_cannot_allocate_if_available_less_than_required():
    small_batch, large_line = make_batch_and_line("E", 20, 25)
    assert small_batch.can_allocate(large_line) is False


def test_cannot_allocate_if_skus_do_not_match():
    batch = Batch("batch-001", "Chair", 1000)
    line = OrderLine("order-001", "Table", 10)
    assert batch.can_allocate(line) is False


def test_can_only_deallocate_allocated_lines():
    batch, line = make_batch_and_line("Table", 20, 2)
    batch.deallocate(line)
    assert batch._purchased_quantity == 20
