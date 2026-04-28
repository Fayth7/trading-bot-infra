#!/bin/bash
# Deployment script for GCP VM

set -e

echo "Deploying ETH/USDT Trading Bot..."

# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install dependencies
sudo apt-get install -y python3-pip python3-venv git build-essential

# Install TA-Lib
sudo apt-get install -y libta-lib0 libta-lib-dev

# Clone repository
cd /opt
sudo rm -rf trading-bot-infra
sudo git clone https://github.com/Fayth7/trading-bot-infra.git
cd trading-bot-infra

# Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install python-dotenv

# Create directories
mkdir -p logs data backups

# Copy .env file (you'll need to create this manually)
if [ ! -f .env ]; then
    echo " Please create .env file with your API keys"
    exit 1
fi

# Setup systemd service
sudo cp systemd/trading-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable trading-bot
sudo systemctl start trading-bot

echo "Deployment complete!"
echo "Check status: sudo systemctl status trading-bot"
echo "View logs: sudo journalctl -u trading-bot -f"