FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create necessary directories
RUN mkdir -p logs aircraft_data

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV TZ=America/New_York

# Health check
HEALTHCHECK --interval=5m --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8080/health', timeout=3)" || exit 1

# Run the bot
CMD ["python", "bot.py"]
