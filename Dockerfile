FROM python:3.9-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements_clean.txt .
RUN pip install --no-cache-dir -r requirements_clean.txt

# Copy application code
COPY main.py .

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "main.py"]
