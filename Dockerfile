FROM python:3.11-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1

# Install minimal system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Use PORT env var set by Render (default 10000 for some platforms), fall back to 8080
ENV PORT=10000
EXPOSE ${PORT}

CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT} app:app"]
