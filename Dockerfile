# Use an official Python runtime as a parent image
FROM python:3.12-alpine

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

# Make port 9090 available to the world outside this container
EXPOSE 9090

# Define environment variable
ENV PYTHONUNBUFFERED=1

# Run the application with live reload for development (optional)
CMD ["uvicorn", "service_check:app", "--host", "0.0.0.0", "--port", "9090"]
