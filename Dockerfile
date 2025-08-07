# Use a Python 3.10 slim base image
FROM python:3.10-slim

# Set environment variables to avoid interactive prompts and define paths
ENV DEBIAN_FRONTEND=noninteractive
ENV CHROME_BIN=/usr/bin/google-chrome
ENV CHROMEDRIVER_PATH=/usr/local/bin/chromedriver

# Install core dependencies for Chrome and other tools
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
    unzip \
    fonts-liberation \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libc6 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libexpat1 \
    libfontconfig1 \
    libgbm1 \
    libgcc1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libstdc++6 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    lsb-release \
    xdg-utils \
    --no-install-recommends && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Google Chrome from the official source
RUN curl -O https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt-get update && \
    apt-get install -y ./google-chrome-stable_current_amd64.deb && \
    rm google-chrome-stable_current_amd64.deb

# Install the matching ChromeDriver version
# The previous command failed because the specific Chrome version (e.g., 139.0.7258)
# often doesn't have a direct LATEST_RELEASE file. This updated command gets
# the major version of Chrome and then finds the latest compatible Chromedriver.
RUN apt-get update && apt-get install -y --no-install-recommends unzip ca-certificates && \
    CHROME_VERSION=$(google-chrome --version | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+') && \
    CHROME_MAJOR_VERSION=$(echo "$CHROME_VERSION" | cut -d '.' -f 1) && \
    echo "Detected Chrome version: $CHROME_VERSION" && \
    echo "Detected Chrome major version: $CHROME_MAJOR_VERSION" && \
    CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_MAJOR_VERSION") && \
    echo "Using Chromedriver version: $CHROMEDRIVER_VERSION" && \
    wget -q "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip" && \
    unzip chromedriver_linux64.zip && \
    mv chromedriver /usr/local/bin/chromedriver && \
    chmod +x /usr/local/bin/chromedriver && \
    rm chromedriver_linux64.zip

# Install Python dependencies from requirements.txt
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy application files and set the working directory
COPY . /app
WORKDIR /app

# Define the default command to run the Python script
CMD ["python", "grays_scraper_cloud.py"]
