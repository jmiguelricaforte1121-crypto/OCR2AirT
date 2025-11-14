# Use a slim Python image
FROM python:3.11-slim

# Install system packages: tesseract + poppler
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Copy dependencies
COPY requirements.txt .

# Install Python deps
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Env vars (optional)
ENV TESSERACT_CMD=/usr/bin/tesseract
# POPLER_BIN left empty: pdf2image will use pdftoppm from PATH

# Expose port (for local clarity; Render uses $PORT)
EXPOSE 5000

# Start with gunicorn on 0.0.0.0:$PORT
CMD ["bash", "-lc", "gunicorn main:app --bind 0.0.0.0:${PORT:-5000}"]
