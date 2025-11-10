FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml poetry.lock* requirements.txt* /app/

RUN if [ -f "poetry.lock" ]; then pip install poetry && poetry install --no-dev; elif [ -f "requirements.txt" ]; then pip install --no-cache-dir -r requirements.txt; fi

COPY . /app

ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]

