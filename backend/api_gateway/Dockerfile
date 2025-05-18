FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml .
COPY README.md .

# Install the package with production dependencies
RUN pip install --no-cache-dir -e .

# Copy application code
COPY . .

# Run the application
CMD ["uvicorn", "backend.api_gateway.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
