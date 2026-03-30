import datetime

from fastapi import Body, FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .config import get_postgres_uri
from .models import Batch, OrderLine
from .orm import start_mappers
from .repository import SqlAlchemyRepository
from .service import add_batch, allocate

start_mappers()
get_session = sessionmaker(bind=create_engine(get_postgres_uri()))
app = FastAPI(debug=True)


def is_valid_sku(sku, batches: list[Batch]):
    return sku in {b.sku for b in batches}


@app.post("/allocate")
async def allocate_endpoint(
    orderid: str = Body(...), sku: str = Body(...), qty: int = Body(...)
):
    session = get_session()
    repo = SqlAlchemyRepository(session)
    line = OrderLine(orderid, sku, qty)

    try:
        batchref = allocate(line=line, repo=repo, session=session)
    except Exception as e:
        return JSONResponse(content={"message": str(e)}, status_code=400)

    return JSONResponse(status_code=201, content={"batchref": batchref})


@app.post("/add_batch")
def add_batch_endpoint(
    ref: str = Body(...),
    sku: str = Body(...),
    qty: int = Body(...),
    eta: datetime.date | None = Body(...),
):
    session = get_session()
    repo = SqlAlchemyRepository()

    add_batch(ref, sku, qty, eta, repo, session)
    return JSONResponse(content="OK", status_code=201)
