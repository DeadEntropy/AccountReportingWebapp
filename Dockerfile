# Use a base Python image
FROM python:3.11-slim

# Install Git
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application into the container
COPY . .

# Expose the port the app will run on
EXPOSE 8050

# Drop root: the app only ever reads /data and serves HTTP, so it needs no write access to /app.
RUN useradd --create-home --uid 10001 appuser && chown -R appuser:appuser /app
USER appuser

# Command to run the Dash app
CMD ["python", "app.py"]