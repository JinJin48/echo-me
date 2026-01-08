FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Set environment variable
ENV PORT=8080

# Expose port (documentation only)
EXPOSE 8080

# Run the application using shell form to expand $PORT
CMD exec functions-framework --target=http_handler --port=$PORT
