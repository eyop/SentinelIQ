FROM python:3.11-slim as base

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install system deps needed for some Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install runtime dependencies early to take advantage of cache
COPY pyproject.toml pyproject.toml
COPY requirements.txt requirements.txt
RUN pip install --upgrade pip && pip install --no-cache-dir .

# Copy application sources
COPY . .

# Create a non-root user and adjust permissions
RUN groupadd -g 1000 appuser || true \
 && useradd -m -u 1000 -g 1000 appuser || true \
 && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
