FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./backend_requirements.txt
RUN pip install --no-cache-dir -r backend_requirements.txt
COPY . .

# In Railway, the app must listen on the port provided by the environment variable
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
