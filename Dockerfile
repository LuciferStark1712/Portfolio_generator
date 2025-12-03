# Use a lightweight Python base image
FROM python:3.9-slim

# Install system dependencies required for Tesseract and PDF processing
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Create necessary directories for file uploads/generation
RUN mkdir -p __DATA__ generated_sites

# Expose the port the app runs on
EXPOSE 8000

# Command to run the app using Gunicorn
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8000", "--timeout", "120"]