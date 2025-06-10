# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables to prevent Python from writing pyc files to disc and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies if any (e.g., for psycopg2 if not binary, or other libraries)
# RUN apt-get update && apt-get install -y some-package

# Install Python dependencies
# Copy only requirements.txt first to leverage Docker cache
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
# This includes the app directory, main.py, etc.
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Define the command to run the application
# Use 0.0.0.0 to make it accessible from outside the container
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
