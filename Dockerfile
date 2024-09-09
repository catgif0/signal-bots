# Use an official Python runtime as a parent image
FROM python:3.8-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Install required Python packages from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 8080 to the outside world
EXPOSE 8080

# Command to run the Uvicorn server to serve the FastAPI application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
