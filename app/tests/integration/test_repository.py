from sqlalchemy import text
from sqlalchemy.orm import Session

from app.domain.models import Batch
from app.adapters.repository import SqlAlchemyRepository


def test_repository_can_save_a_batch(session: Session):
    batch = Batch("batch1", "RUSTY-SOAPDISH", 100, eta=None)

    repo = SqlAlchemyRepository(session)
    repo.add(batch)
    session.commit()

    rows = session.execute(
        text('SELECT reference, sku, _purchased_quantity, eta FROM "batches"')
    )
    assert list(rows) == [("batch1", "RUSTY-SOAPDISH", 100, None)]
