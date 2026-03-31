import datetime

from fastapi import Body, FastAPI, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .adapters.orm import start_mappers
from .config import get_postgres_uri
from .domain.models import Batch
from .service_layer.service import add_batch, allocate
from .service_layer.unit_of_work import SqlAlchemyUnitOfWork

start_mappers()
get_session = sessionmaker(bind=create_engine(get_postgres_uri()))
app = FastAPI(debug=True)


def is_valid_sku(sku, batches: list[Batch]):
    return sku in {b.sku for b in batches}


@app.post("/allocate")
async def allocate_endpoint(
    orderid: str = Body(...), sku: str = Body(...), qty: int = Body(...)
):
    uow = SqlAlchemyUnitOfWork()
    try:
        batchref = allocate(orderid, sku, qty, uow)
    except Exception as e:
        # return JSONResponse(content={"message": str(e)}, status_code=400)
        raise HTTPException(status_code=400, detail=str(e))
    return JSONResponse(status_code=201, content={"batchref": batchref})


@app.post("/add_batch")
def add_batch_endpoint(
    ref: str = Body(...),
    sku: str = Body(...),
    qty: int = Body(...),
    eta: datetime.date | None = Body(None),
):
    uow = SqlAlchemyUnitOfWork()
    add_batch(ref, sku, qty, eta, uow)
    return JSONResponse(content="OK", status_code=201)
