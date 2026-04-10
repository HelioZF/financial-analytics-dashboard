# ---------- Stage 1: build dependencies ----------
FROM python:3.11-slim AS builder

WORKDIR /build

RUN pip install --no-cache-dir --upgrade pip

COPY pyproject.toml ./
RUN pip install --no-cache-dir --prefix=/install .

# ---------- Stage 2: runtime ----------
FROM python:3.11-slim AS runtime

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY app/ ./app/
COPY seed/ ./seed/
COPY migrations/ ./migrations/

EXPOSE 3200

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3200"]
