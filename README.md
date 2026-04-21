# ETH/USDT Trading Bot with Auto-Earn

**Production-grade cryptocurrency trading bot** running 24/7 on Google Cloud VM with 99.9% uptime.

## Features

- **Automated Trading**: RSI-based DCA strategy with trailing stops
- **Binance Earn Integration**: Auto-subscribe idle funds for passive yield
- **24/7 Monitoring**: Email alerts, logging, performance reports
- **Production Ready**: Systemd service, health checks
- **Risk Management**: Position limits, cooldowns

## Performance

| Metric | Value |
|--------|-------|
| Uptime | 99.9% (7+ months) |
| Capital | $3,000 |
| Weekly Revenue | $200-300 |
| Active Trades | Max 4 positions |

## Quick Start

### Prerequisites
- Python 3.9+
- Binance API key (with Earn permissions)
- Gmail account for alerts

### One-Command Setup

```bash
git clone https://github.com/Fayth7/trading-bot-infra.git
cd trading-bot-infra
cp .env.example .env
# Edit .env with your API keys
make setup
make run

Or Manual Setup
bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env  # Add your Binance API keys

# Run the bot
python bot/main.py

# Project Structure

trading-bot-infra/
├── bot/           # Core trading logic
├── config/        # Configuration management
├── scripts/       # Deployment & monitoring
├── tests/         # Unit tests
└── systemd/       # Service configuration

 Configuration
Edit .env file:

BINANCE_API_KEY=your_key_here
BINANCE_SECRET_KEY=your_secret_here
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
TRADE_AMOUNT=3000.0
RSI_BUY_THRESHOLD=30
PROFIT_TARGET=0.05 (Adjust as required)


# Security
API keys restricted to trading & Earn permissions only

No withdrawal permissions

Environment variables (never hardcoded)

Encrypted credential storage

Author
Faith Ampwera - DevOps Backend Engineer

LinkedIn - https://github.com/Fayth7

GitHub - https://www.linkedin.com/in/faith-ampwera-841a7638/

⭐ Star this repo if you find it useful!