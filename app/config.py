def get_api_url() -> str:
    return "http://localhost:8000"


def get_postgres_uri():
    # postgres is the default database
    # it automatically creates as the user_name
    return "postgresql://postgres:secret@localhost:5432/postgres"
