"""
Configuration management for ETH/USDT Trading Bot
Loads from environment variables with sensible defaults
"""

import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class TradingConfig:
    """Trading parameters"""
    
    # Trading pair
    TRADING_PAIR = os.getenv('TRADING_PAIR', 'ETH/USDT')
    
    # Money management
    INITIAL_TRADE_AMOUNT = float(os.getenv('INITIAL_TRADE_AMOUNT', '3000.0'))
    REINVEST_RATIO = float(os.getenv('REINVEST_RATIO', '1.0'))
    MAX_ACTIVE_TRADES = int(os.getenv('MAX_ACTIVE_TRADES', '4'))
    
    # Technical indicators
    RSI_BUY_THRESHOLD = int(os.getenv('RSI_BUY_THRESHOLD', '30'))
    EMA_PERIOD = int(os.getenv('EMA_PERIOD', '20'))
    
    # Profit taking
    PROFIT_TARGET = float(os.getenv('PROFIT_TARGET', '0.01'))
    TRAILING_PROFIT_PERCENT = float(os.getenv('TRAILING_PROFIT_PERCENT', '0.001'))
    TRAILING_ACTIVATION_BUFFER = float(os.getenv('TRAILING_ACTIVATION_BUFFER', '0.001'))
    
    # Timing
    CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '30'))
    TRADE_COOLDOWN = int(os.getenv('TRADE_COOLDOWN', '7200'))
    TIMEOUT_HOURS = int(os.getenv('TIMEOUT_HOURS', '72'))
    
    # Bot identification
    BOT_ID = os.getenv('BOT_ID', 'ETHUSDT_01')


class BinanceConfig:
    """Binance exchange configuration"""
    
    API_KEY = os.getenv('BINANCE_API_KEY')
    SECRET_KEY = os.getenv('BINANCE_SECRET_KEY')
    
    # Earn products
    FLEXIBLE_EARN_PRODUCTS = {
        'ETH': 'ETH001',
        'USDT': 'USDT001'
    }
    
    MINIMUM_SUBSCRIPTION = {
        'ETH': float(os.getenv('MINIMUM_SUBSCRIPTION_ETH', '0.001')),
        'USDT': float(os.getenv('MINIMUM_SUBSCRIPTION_USDT', '10.0'))
    }
    
    REDEMPTION_DELAY = int(os.getenv('REDEMPTION_DELAY', '2'))


class EmailConfig:
    """Email alert configuration"""
    
    EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
    RECIPIENT_EMAILS = [e.strip() for e in os.getenv('RECIPIENT_EMAILS', '').split(',') if e.strip()]


class FileConfig:
    """File paths for data storage"""
    
    LOG_FILE = "logs/ethusdt.txt"
    EXCEL_FILE = "logs/ethusdt.xlsx"
    ERROR_LOG_FILE = "logs/ethusdt_errors.txt"
    ACTIVE_TRADES_FILE = "data/active_trades.json"
    EARN_REPORT_FILE = "logs/earn_ethusdt.txt"
    EARN_EXCEL_FILE = "logs/earn_ethusdt.xlsx"


# Validation
def validate_config():
    """Check if critical config is present"""
    errors = []
    
    if not BinanceConfig.API_KEY or BinanceConfig.API_KEY == 'your_api_key_here':
        errors.append("BINANCE_API_KEY not set in .env")
    
    if not BinanceConfig.SECRET_KEY or BinanceConfig.SECRET_KEY == 'your_secret_key_here':
        errors.append("BINANCE_SECRET_KEY not set in .env")
    
    if errors:
        raise ValueError(f"Configuration errors:\n" + "\n".join(errors))
    
    return True


# Create necessary directories
def init_directories():
    """Create required directories if they don't exist"""
    os.makedirs("logs", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    os.makedirs("backups", exist_ok=True)


# Export all configs
__all__ = [
    'TradingConfig',
    'BinanceConfig', 
    'EmailConfig',
    'FileConfig',
    'validate_config',
    'init_directories'
]