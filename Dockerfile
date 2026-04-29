FROM python:3.11-slim

# Security: run as non-root user
RUN groupadd -r votewise && useradd -r -g votewise votewise

WORKDIR /app

# Install dependencies before copying source to leverage Docker layer cache.
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Copy application source.
COPY app/ ./app/
COPY templates/ ./templates/
COPY main.py .

# Set ownership to non-root user.
RUN chown -R votewise:votewise /app
USER votewise

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

EXPOSE 8080

CMD exec gunicorn \
    --bind "0.0.0.0:${PORT}" \
    --workers 2 \
    --threads 4 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    main:app
