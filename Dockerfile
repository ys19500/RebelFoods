# Start with a lightweight Python image
FROM python:3.11-slim

# Install dependencies without root access
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg2 \
    ca-certificates \
    fonts-liberation \
    libappindicator3-1 \
    libasound2 \
    libx11-xcb1 \
    libxcomposite1 \
    libxrandr2 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Download and install Chrome (no root needed)
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN dpkg -i google-chrome-stable_current_amd64.deb || apt-get install -f -y

# Install your Python dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application
COPY . .

# Expose port 10000 for FastAPI (default port)
EXPOSE 10000

# Start FastAPI app
CMD ["uvicorn", "backend:app", "--host", "0.0.0.0", "--port", "10000"]
