import os


def get_api_url() -> str:
    host = os.environ.get("API_HOST", "localhost")
    port = 8000
    return f"http://{host}:{port}"


def get_postgres_uri():
    password = os.environ.get("POSTGRES_PASSWORD", "secret")
    host = "postgres"
    port = 5432
    return f"postgresql://postgres:{password}@{host}:{port}/postgres"


def get_redis_host_and_port():
    host = os.environ.get("REDIS_HOST", "redis")
    port = 6379
    return {"host": host, "port": port}
