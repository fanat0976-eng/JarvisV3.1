FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[rag]" && \
    pip install --no-cache-dir uvicorn[standard] httpx pyyaml beautifulsoup4 lxml

COPY core/ core/
COPY plugins/ plugins/
COPY web/ web/
COPY data/ data/

ENV PYTHONUNBUFFERED=1

EXPOSE 8003

CMD ["python", "core/server.py"]
