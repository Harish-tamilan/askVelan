# Use the official Python image from the Docker Hub
FROM python:3.8-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies and build tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libpoppler-cpp-dev \
        wget \
        libglib2.0-0 \
        libsm6 \
        libxrender1 \
        libxext6 \
        && apt-get clean \
        && rm -rf /var/lib/apt/lists/*

# Copy the current directory contents into the container at /app
COPY . /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Run app.py when the container launches
CMD ["python", "app.py"]
