from abc import ABC, abstractmethod

from sqlalchemy.orm import Session
from sqlalchemy import orm

from ..domain.models import Product, Batch


class AbstractRepository(ABC):
    def __init__(self):
        self.seen: set[Product] = set()

    def add(self, product: Product):
        self._add(product)
        self.seen.add(product)

    def get(self, sku: str) -> Product:
        product = self._get(sku)
        if product:
            self.seen.add(product)
        return product

    def get_by_batchref(self, batchref: str) -> Product:
        product = self._get_by_batchref(batchref)
        if product:
            self.seen.add(product)
        return product

    @abstractmethod
    def _add(self, product: Product):
        raise NotImplementedError

    @abstractmethod
    def _get(self, sku) -> Product:
        raise NotImplementedError

    @abstractmethod
    def _get_by_batchref(self, batchref: str) -> Product:
        raise NotImplementedError


class SqlAlchemyRepository(AbstractRepository):
    def __init__(self, session: Session):
        super().__init__()
        self.session = session

    def _add(self, product: Product):
        self.session.add(product)

    def _get(self, sku):
        return self.session.query(Product).filter_by(sku=sku).first()

    def _get_by_batchref(self, batchref):
        return (
            self.session.query(Product)
            .join(Batch)
            .filter(orm.batches.c.reference == batchref)
            .first()
        )
