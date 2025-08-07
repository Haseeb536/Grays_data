# Use official slim Python image
FROM python:3.10-slim

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    git \
    fonts-liberation \
    libnss3 \
    libatk-bridge2.0-0 \
    libxss1 \
    libasound2 \
    libgbm1 \
    libgtk-3-0 \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Set environment variables required by Selenium
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/lib/chromium/chromedriver
ENV PATH=$CHROMEDRIVER_PATH:$PATH

# Run your scraping script
CMD ["python", "grays_scraper_cloud.py"]
