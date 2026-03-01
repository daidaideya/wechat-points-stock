# Use an official Python runtime as a parent image
FROM docker.1ms.run/library/python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

# Make port 5711 available to the world outside this container
EXPOSE 5711

# Define environment variable
ENV PYTHONPATH=/app

# Create necessary directories
RUN mkdir -p logs data static/uploads

# Make entrypoint script executable
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Run entrypoint script when the container launches
CMD ["./entrypoint.sh"]
