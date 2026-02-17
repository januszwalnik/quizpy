FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for X11 and GUI
RUN apt-get update && apt-get install -y \
    tk \
    tcl \
    xauth \
    libx11-6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "app.py"]
