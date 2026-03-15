# Use Python 3.11 slim as the base image for a small footprint
FROM python:3.11-slim

# Set environment variables to prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create and set the working directory
WORKDIR /app

# Install system dependencies if required (e.g., for building some C-extensions)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file to install dependencies
COPY requirements.txt /app/

# Install the Python dependencies and gunicorn for production deployment
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy the rest of the application code
COPY . /app/

# Create a non-root user for security
RUN useradd -m myuser && chown -R myuser:myuser /app
USER myuser

# Expose the application port
EXPOSE 5000

# Set environment variables for the application
ENV PORT=5000

# Run the application with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:create_app()"]
