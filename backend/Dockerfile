FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root system user and group
RUN groupadd -g 10001 sentinelops && \
    useradd -u 10001 -g sentinelops -m -s /bin/bash sentinelops

COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Ensure mako template is present for autogenerate
RUN test -f ./alembic/script.py.mako || printf '%s\n' '${up_revision}' > /dev/null

# Set ownership to non-root user
RUN mkdir -p /app/data && chown -R sentinelops:sentinelops /app

ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

USER sentinelops

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/ready', timeout=3)" || exit 1

CMD ["uvicorn", "sentinelops.main:app", "--host", "0.0.0.0", "--port", "8000"]
