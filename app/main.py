from fastapi import FastAPI

app = FastAPI()


@app.get("/allocate")
def allocate_endpoint():
    pass
