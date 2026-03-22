# ---- Builder Stage ----
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Copy requirements and install into a virtual environment
COPY requirements.txt .
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# Copy the full source code
COPY . .

# ---- Final Stage ----
FROM python:3.11-slim

# Create a non-root user for security
RUN useradd --create-home appuser
USER appuser
WORKDIR /home/appuser/app
RUN mkdir -p /home/appuser/app/logs

# Copy the virtual environment from the builder
COPY --from=builder /opt/venv /opt/venv

# Copy the application code
COPY --from=builder /app /home/appuser/app

# Use the virtual environment binaries
ENV PATH="/opt/venv/bin:$PATH"

EXPOSE 8000

CMD ["python", "run.py"]
