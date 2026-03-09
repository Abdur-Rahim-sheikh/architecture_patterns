from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import config
from .models import OrderLine, allocate, Batch
import orm
import repository


orm.start_mappers()
get_session = sessionmaker(bind=create_engine(config.get_postgres_uri()))
app = FastAPI()


def is_valid_sku(sku, batches: list[Batch]):
    return sku in {b.sku for b in batches}


@app.post("/allocate")
async def allocate_endpoint(request: Request):
    request = await request.json()
    session = get_session()
    batches = repository.SqlAlchemyRepository(session).list()
    line = OrderLine(request["orderid"], request["sku"], request["qty"])

    if not is_valid_sku(line.sku, batches):
        return JSONResponse(
            content={"message": f"Invalid sku {line.sku}"}, status_code=400
        )
    try:
        batchref = allocate(line=line, batches=batches)
    except Exception as e:
        return JSONResponse(content={"message": str(e)}, status_code=400)

    return JSONResponse(status_code=201, content={"batchref": batchref})
