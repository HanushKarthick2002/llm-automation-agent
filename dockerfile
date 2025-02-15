# Use an official Python runtime as the base image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED 1

# Install required packages
RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the app files into the container
COPY . /app
WORKDIR /app

# Expose the API port
EXPOSE 8000

# Command to run the FastAPI app
CMD ["uvicorn", "post2:app", "--host", "0.0.0.0", "--port", "8001"]
