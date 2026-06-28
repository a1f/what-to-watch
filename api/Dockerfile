# syntax=docker/dockerfile:1
# Build context is the REPO ROOT (the Python project lives at the root).
FROM python:3.12-slim

# uv installs dependencies reproducibly from the committed uv.lock.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1

WORKDIR /app

# Install inputs first, then the package source, then sync (runtime deps only).
COPY pyproject.toml uv.lock alembic.ini ./
COPY api ./api
RUN uv sync --frozen --no-dev

# Put the synced venv on PATH so we exec the built binaries directly (no `uv run`,
# which would re-validate the lockfile's default groups — incl. dev — at start).
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

# Bare image just serves; compose overrides this to run `alembic upgrade head` first.
CMD ["uvicorn", "api.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
