FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    gdal-bin \
    libgdal-dev \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml requirements.txt README.md ./
COPY compass_core/ compass_core/
COPY cli/ cli/
COPY config/ config/
COPY api/ api/
COPY app/ app/

RUN pip install --no-cache-dir -e ".[all]" \
    || pip install --no-cache-dir -r requirements.txt

ENV PYTHONUNBUFFERED=1
EXPOSE 8000 8501

CMD ["python", "-m", "cli.main", "demo", "--model", "woe"]
