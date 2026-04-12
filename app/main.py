import datetime

from fastapi import Body, FastAPI, HTTPException
from fastapi.responses import JSONResponse

from . import bootstrap, views
from .domain.commands import Allocate, CreateBatch
from .domain.models import Batch

bus = bootstrap.bootstrap()
# metadata.create_all(bind=create_engine(get_postgres_uri()))
app = FastAPI(debug=True)


def is_valid_sku(sku, batches: list[Batch]):
    return sku in {b.sku for b in batches}


@app.post("/allocate")
async def allocate_endpoint(
    orderid: str = Body(...), sku: str = Body(...), qty: int = Body(...)
):
    try:
        message = Allocate(orderid, sku, qty)
        bus.handle(message=message)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return JSONResponse(status_code=202, content="ok")


@app.get("/allocations")
def allocations_view_endpoint(orderid: str):
    # uow = SqlAlchemyUnitOfWork()
    result = views.allocations(orderid)

    if not result:
        raise HTTPException(status_code=404, detail="orderid not found")

    return JSONResponse(content=result)


@app.post("/add_batch")
def add_batch_endpoint(
    ref: str = Body(...),
    sku: str = Body(...),
    qty: int = Body(...),
    eta: datetime.date | None = Body(None),
):
    message = CreateBatch(ref, sku, qty, eta)
    bus.handle(message=message)
    return JSONResponse(content="OK", status_code=201)
