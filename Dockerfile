# ---------- Stage 1: build dependencies ----------
FROM python:3.11-slim AS builder

WORKDIR /build

RUN pip install --no-cache-dir --upgrade pip

COPY pyproject.toml ./
# Dev extras (pytest, httpx, ruff) are bundled into the image so the same
# image can run the test suite via `docker compose exec app pytest`.
# For a stricter prod deployment, split into two build targets later.
RUN pip install --no-cache-dir --prefix=/install ".[dev]"

# ---------- Stage 2: runtime ----------
FROM python:3.11-slim AS runtime

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code + tests + project metadata (pyproject.toml carries
# the [tool.pytest.ini_options] config used by `docker compose exec app pytest`)
COPY app/ ./app/
COPY seed/ ./seed/
COPY migrations/ ./migrations/
COPY tests/ ./tests/
COPY pyproject.toml ./

EXPOSE 3200

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3200"]
