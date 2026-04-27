# Use official Python image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose Streamlit port
EXPOSE 8502

# Healthcheck
HEALTHCHECK CMD curl --fail http://localhost:8502/_stcore/health

# Run the app
ENTRYPOINT ["streamlit", "run", "src/bot_dashboard.py", "--server.port=8502", "--server.address=0.0.0.0"]
