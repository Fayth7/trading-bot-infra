FROM python:3.9-slim

WORKDIR /app

# Install TA-Lib system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libta-lib0 \
    libta-lib-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install python-dotenv

# Copy application
COPY . .

# Create necessary directories
RUN mkdir -p logs data backups

# Run bot
CMD ["python", "bot/main.py"]