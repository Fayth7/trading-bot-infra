"""
Binance Earn integration - auto-subscribe idle funds
"""

import time
from config.settings import BinanceConfig, TradingConfig


class EarnManager:
    """Manage Binance Simple Earn subscriptions"""
    
    def __init__(self, exchange):
        self.exchange = exchange
    
    def get_balance(self, asset='ETH'):
        """Get total balance for asset in Earn"""
        try:
            if asset not in BinanceConfig.FLEXIBLE_EARN_PRODUCTS:
                return 0.0
            
            positions = self.exchange.sapi_get_simple_earn_flexible_position({
                'asset': asset
            })
            
            if not positions or 'rows' not in positions:
                return 0.0
            
            total = sum(float(p['totalAmount']) for p in positions['rows'])
            return total
            
        except Exception as e:
            print(f"Error getting {asset} Earn balance: {e}")
            return 0.0
    
    def subscribe(self, asset, amount, client_tag=None):
        """Subscribe assets to Simple Earn"""
        try:
            min_amount = BinanceConfig.MINIMUM_SUBSCRIPTION.get(asset, 0)
            if float(amount) < min_amount:
                print(f"Amount {amount} below minimum {min_amount} for {asset}")
                return False
            
            product_id = BinanceConfig.FLEXIBLE_EARN_PRODUCTS.get(asset)
            if not product_id:
                print(f"No product ID found for {asset}")
                return False
            
            subscribe_params = {
                'productId': product_id,
                'amount': float(amount),
                'recvWindow': 10000
            }
            
            if client_tag:
                subscribe_params['clientTag'] = client_tag
            
            result = self.exchange.sapi_post_simple_earn_flexible_subscribe(subscribe_params)
            print(f"Subscribed {amount:.2f} {asset} to Earn")
            return True
            
        except Exception as e:
            print(f"Failed to subscribe {asset} to Earn: {e}")
            return False
    
    def redeem(self, asset, amount):
        """Redeem from Earn with proper formatting"""
        try:
            product_id = BinanceConfig.FLEXIBLE_EARN_PRODUCTS.get(asset)
            if not product_id:
                print(f"No product ID found for {asset}")
                return False
            
            # Format amount without scientific notation
            amount_str = format(float(amount), '.8f').rstrip('0').rstrip('.')
            
            result = self.exchange.sapi_post_simple_earn_flexible_redeem({
                'productId': str(product_id),
                'amount': amount_str,
                'type': 'FAST',
                'recvWindow': 10000
            })
            
            print(f"Redeemed {amount_str} {asset} from Earn")
            time.sleep(BinanceConfig.REDEMPTION_DELAY)
            return True
            
        except Exception as e:
            print(f"Failed to redeem {asset} from Earn: {e}")
            return False