"""
Utility functions for trading bot
"""

import os
import time
import json
import shutil
from datetime import datetime
import pytz

# Timezone
EAT = pytz.timezone('Africa/Nairobi')


def get_timestamp_eat():
    """Get current timestamp in East Africa Time"""
    return datetime.now(EAT)


def format_datetime_eat(dt=None):
    """Format datetime in EAT timezone"""
    if dt is None:
        dt = datetime.now(EAT)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def ensure_directories():
    """Create all required directories"""
    dirs = ['logs', 'data', 'backups']
    for d in dirs:
        os.makedirs(d, exist_ok=True)


def backup_file(filepath, backup_dir="backups"):
    """Create timestamped backup of a file"""
    if not os.path.exists(filepath):
        return None
    
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    basename = os.path.basename(filepath)
    backup_path = os.path.join(backup_dir, f"{basename}_{timestamp}.bak")
    
    shutil.copy2(filepath, backup_path)
    return backup_path


def safe_json_load(filepath, default=None):
    """Safely load JSON file, return default if error"""
    if not os.path.exists(filepath):
        return default if default is not None else {}
    
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return default if default is not None else {}


def safe_json_save(data, filepath, indent=2):
    """Safely save JSON with atomic write"""
    temp_file = f"{filepath}.tmp"
    backup_file = f"{filepath}.bak"
    
    try:
        # Write to temp file
        with open(temp_file, 'w') as f:
            json.dump(data, f, indent=indent, default=str)
        
        # Backup existing
        if os.path.exists(filepath):
            shutil.copy2(filepath, backup_file)
        
        # Atomic rename
        shutil.move(temp_file, filepath)
        return True
    
    except Exception as e:
        print(f"Error saving {filepath}: {e}")
        return False


def calculate_profit_pct(buy_price, current_price):
    """Calculate profit percentage"""
    return (current_price - buy_price) / buy_price * 100


def format_currency(value):
    """Format USD currency"""
    return f"${value:,.2f}"


def format_eth(value):
    """Format ETH with 4 decimal places"""
    return f"{value:.4f} ETH"