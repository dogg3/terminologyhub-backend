# Use the official Python 3.11 image from Docker Hub
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies, including SQLite
RUN apt-get update && apt-get install -y sqlite3

# Install pipenv
RUN pip install pipenv

# Copy the Pipfile and Pipfile.lock into the container
COPY Pipfile Pipfile.lock ./

# Install dependencies via Pipenv
RUN pipenv install --system --deploy

# Copy the application code into the container
COPY app /app

# Copy schema file and entrypoint script
COPY schema.sql /app/
COPY entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

# Expose the application on port 8080
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
