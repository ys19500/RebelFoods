# Use a Python base image
FROM python:3.11-slim-buster

# Install system dependencies for Chrome.  We install these in the backend
# container because that's where our scraping logic resides.  The Selenium
# container we'll use from Docker Hub already has its browser.
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    curl \
    unzip \
    ca-certificates \
    libx11-dev \
    libgconf-2-4 \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libgbm1 \
    libasound2 \
    google-chrome-stable \
    && apt-get clean \
    && rm -rf /var/cache/apt

# Set Chrome binary path
ENV CHROME_BIN=/usr/bin/google-chrome-stable

# Set working directory
WORKDIR /app

# Copy the requirements file and install the Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app code
COPY . /app

# Expose the port your application uses
EXPOSE 8000  # Changed to 8000, a more standard port for web applications

# Use the correct command to start your application.
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"] #Make sure app:app is correct
