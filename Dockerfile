FROM python:3.12-slim

# Install system dependencies including libsqlite3
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsqlite3-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Fly will set $PORT
ENV PORT=8080
EXPOSE 8080

CMD uvicorn web:app --host 0.0.0.0 --port $PORT