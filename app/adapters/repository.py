from abc import ABC, abstractmethod

from sqlalchemy.orm import Session

from ..domain.models import Product


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

    @abstractmethod
    def _add(self, product: Product):
        raise NotImplementedError

    @abstractmethod
    def _get(self, sku) -> Product:
        raise NotImplementedError


class SqlAlchemyRepository(AbstractRepository):
    def __init__(self, session: Session):
        super().__init__()
        self.session = session

    def _add(self, product: Product):
        self.session.add(product)

    def _get(self, sku):
        return self.session.query(Product).filter_by(sku=sku).first()
