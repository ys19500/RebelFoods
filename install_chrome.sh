#!/bin/bash

# Install dependencies without root
apt-get update
apt-get install -y wget curl gnupg2 ca-certificates libx11-xcb1 libxcomposite1 libxrandr2 xdg-utils

# Install Chrome in user space (no root required)
CHROME_VERSION="google-chrome-stable_current_amd64.deb"
wget https://dl.google.com/linux/direct/$CHROME_VERSION
dpkg -i $CHROME_VERSION || apt-get install -f -y

# Clean up
rm $CHROME_VERSION

# Check installation
google-chrome-stable --version
