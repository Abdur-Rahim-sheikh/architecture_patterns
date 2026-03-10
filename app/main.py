from fastapi import FastAPI, Body
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .config import get_postgres_uri
from .models import Batch, OrderLine, allocate
from .orm import start_mappers
from .repository import SqlAlchemyRepository

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
    batches = SqlAlchemyRepository(session).list()
    line = OrderLine(orderid, sku, qty)

    if not is_valid_sku(line.sku, batches):
        return JSONResponse(
            content={"message": f"Invalid sku {line.sku}"}, status_code=400
        )
    try:
        batchref = allocate(line=line, batches=batches)
    except Exception as e:
        return JSONResponse(content={"message": str(e)}, status_code=400)

    session.commit()
    return JSONResponse(status_code=201, content={"batchref": batchref})
