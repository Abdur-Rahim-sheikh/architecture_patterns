from abc import ABC, abstractmethod

from sqlalchemy.orm import Session

from ..domain.models import Batch, Product


class AbstractRepository(ABC):
    @abstractmethod
    def add(self, batch: Batch):
        raise NotImplementedError

    @abstractmethod
    def get(self, sku) -> Batch:
        raise NotImplementedError

    @abstractmethod
    def list(self):
        raise NotImplementedError


class SqlAlchemyRepository(AbstractRepository):
    def __init__(self, session: Session):
        self.session = session

    def add(self, batch):
        self.session.add(batch)

    def get(self, sku):
        return self.session.query(Batch).filter_by(sku=sku).one()

    def list(self):
        return self.session.query(Batch).all()


class AbstractProductRepository(ABC):
    @abstractmethod
    def add(self, product: Product):
        raise NotImplementedError

    @abstractmethod
    def get(self, sku) -> Product:
        raise NotImplementedError
