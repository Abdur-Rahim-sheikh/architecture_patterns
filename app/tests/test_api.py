from ..repository import FakeRepository
from ..models import Batch

batch1 = Batch("Balls", "sku-1", 5)
batch2 = Batch("Balls", "sku-2", 15)
batch3 = Batch("Balls", "sku-1", 50)
fake_repo = FakeRepository([batch1, batch2, batch3])
