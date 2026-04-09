FROM python:3.13-slim-bullseye
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app

COPY pyproject.toml uv.lock .

RUN uv sync --locked

COPY . .


CMD ["uv", "run", "fastapi", "dev"]