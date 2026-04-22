"""
Core trading logic - buy and sell execution
"""

import time
import json
from datetime import datetime
from config.settings import TradingConfig, BinanceConfig, FileConfig
from bot.utils import safe_json_save, safe_json_load, get_timestamp_eat
from bot.earn import EarnManager


class TradeManager:
    """Manage active trades and trade execution"""
    
    def __init__(self, exchange):
        self.exchange = exchange
        self.earn = EarnManager(exchange)
        self.active_trades = {}
        self.trade_counter = 0
        self.last_buy_time = 0
        
        # Financial tracking
        self.total_invested = 0.0
        self.total_withdrawn = 0.0
        self.total_earnings = 0.0
        self.total_profits_reinvested = 0.0
        
        # Load existing trades
        self.load_trades()
    
    def load_trades(self):
        """Load active trades from disk"""
        data = safe_json_load(FileConfig.ACTIVE_TRADES_FILE)
        
        if not data:
            return
        
        # Handle both old and new formats
        if 'active_trades' in data:
            saved_trades = data['active_trades']
            metadata = data.get('metadata', {})
            
            self.total_invested = float(metadata.get('total_invested', 0))
            self.total_withdrawn = float(metadata.get('total_withdrawn', 0))
            self.total_earnings = float(metadata.get('total_earnings', 0))
            self.total_profits_reinvested = float(metadata.get('total_profits_reinvested', 0))
            self.trade_counter = int(metadata.get('trade_counter', 0))
        else:
            saved_trades = data
        
        # Convert string keys back to int if needed
        for trade_id, trade in saved_trades.items():
            self.active_trades[trade_id] = trade
        
        print(f"Loaded {len(self.active_trades)} active trades")
    
    def save_trades(self):
        """Save active trades to disk"""
        data = {
            'active_trades': self.active_trades,
            'metadata': {
                'total_invested': self.total_invested,
                'total_withdrawn': self.total_withdrawn,
                'total_earnings': self.total_earnings,
                'total_profits_reinvested': self.total_profits_reinvested,
                'trade_counter': self.trade_counter,
                'last_save': get_timestamp_eat().isoformat(),
                'version': 2.0
            }
        }
        
        safe_json_save(data, FileConfig.ACTIVE_TRADES_FILE)
    
    def can_buy(self):
        """Check if we can place a new buy order"""
        current_time = time.time()
        
        # Cooldown check
        if current_time - self.last_buy_time < TradingConfig.TRADE_COOLDOWN:
            remaining = int(TradingConfig.TRADE_COOLDOWN - (current_time - self.last_buy_time))
            print(f"Buy cooldown: {remaining}s remaining")
            return False
        
        # Max trades check
        if len(self.active_trades) >= TradingConfig.MAX_ACTIVE_TRADES:
            print(f"Max active trades reached ({len(self.active_trades)}/{TradingConfig.MAX_ACTIVE_TRADES})")
            return False
        
        return True
    
    def execute_buy(self, buy_score, confidence, rsi_value):
        """Execute a market buy order"""
        try:
            # Check USDT balance
            balances = self.exchange.fetch_balance()
            spot_usdt = balances['USDT']['free']
            
            # Calculate trade amount (reinvested profits included)
            trade_amount = TradingConfig.INITIAL_TRADE_AMOUNT / 4 + self.total_profits_reinvested
            
            if spot_usdt < trade_amount:
                # Try to redeem from Earn
                earn_usdt = self.earn.get_balance('USDT')
                needed = trade_amount - spot_usdt
                
                if needed > 0 and earn_usdt >= BinanceConfig.MINIMUM_SUBSCRIPTION['USDT']:
                    if self.earn.redeem('USDT', needed):
                        spot_usdt = self.exchange.fetch_balance()['USDT']['free']
            
            if spot_usdt < trade_amount:
                print(f"Insufficient USDT: ${spot_usdt:.2f} < ${trade_amount:.2f}")
                return False
            
            # Get current price
            ticker = self.exchange.fetch_ticker(TradingConfig.TRADING_PAIR)
            current_price = ticker['last']
            quantity = trade_amount / current_price
            
            # Place market order
            order = self.exchange.create_market_buy_order(TradingConfig.TRADING_PAIR, quantity)
            
            actual_cost = float(order['cost'])
            actual_price = float(order['price'])
            actual_quantity = float(order['filled'])
            
            # Update financial tracking
            self.total_invested += actual_cost
            trade_id = f"TRADE_{self.trade_counter:04d}"
            self.trade_counter += 1
            
            # Create trade record
            self.active_trades[trade_id] = {
                'buy_price': actual_price,
                'quantity': actual_quantity,
                'buy_time': time.time(),
                'current_price': current_price,
                'max_price': current_price,
                'profit_target': actual_price * (1 + TradingConfig.PROFIT_TARGET),
                'trailing_activation_price': actual_price * (1 + TradingConfig.PROFIT_TARGET + 0.001),
                'trailing_activated': False,
                'buy_score': buy_score,
                'entry_rsi': rsi_value,
                'in_earn': False,
                'investment_amount': actual_cost
            }
            
            # Move to Earn if eligible
            if actual_quantity >= BinanceConfig.MINIMUM_SUBSCRIPTION['ETH']:
                if self.earn.subscribe('ETH', actual_quantity, TradingConfig.BOT_ID):
                    self.active_trades[trade_id]['in_earn'] = True
            
            self.last_buy_time = time.time()
            self.save_trades()
            
            print(f" BUY {trade_id}: {actual_quantity:.4f} ETH @ ${actual_price:.2f}")
            return True
            
        except Exception as e:
            print(f"Buy execution failed: {e}")
            return False
    
    def check_sell_conditions(self):
        """Check if any trades meet sell conditions"""
        try:
            ticker = self.exchange.fetch_ticker(TradingConfig.TRADING_PAIR)
            current_price = ticker['last']
            
            trades_to_sell = []
            
            for trade_id, trade in self.active_trades.items():
                buy_price = trade['buy_price']
                current_profit = (current_price - buy_price) / buy_price
                
                # Update max price
                trade['max_price'] = max(trade.get('max_price', buy_price), current_price)
                max_profit = (trade['max_price'] - buy_price) / buy_price
                pullback = (trade['max_price'] - current_price) / trade['max_price']
                
                # Sell condition: profit target reached AND pullback triggered
                if (current_profit >= TradingConfig.PROFIT_TARGET and
                    pullback >= TradingConfig.TRAILING_PROFIT_PERCENT):
                    trades_to_sell.append(trade_id)
            
            return trades_to_sell, current_price
            
        except Exception as e:
            print(f"Error checking sell conditions: {e}")
            return [], 0
    
    def execute_sell(self, trade_ids, current_price):
        """Execute sell orders for given trades"""
        total_profit = 0
        
        for trade_id in trade_ids:
            trade = self.active_trades[trade_id]
            
            try:
                # Redeem from Earn if needed
                if trade.get('in_earn', False):
                    if not self.earn.redeem('ETH', trade['quantity']):
                        print(f"Failed to redeem {trade_id} from Earn")
                        continue
                
                # Execute sell
                order = self.exchange.create_market_sell_order(
                    TradingConfig.TRADING_PAIR,
                    trade['quantity']
                )
                
                sell_price = float(order['price'])
                profit = (sell_price - trade['buy_price']) * trade['quantity']
                total_profit += profit
                self.total_earnings += profit
                
                # Reinvest profits
                reinvest_amount = profit * TradingConfig.REINVEST_RATIO
                self.total_profits_reinvested += reinvest_amount
                
                print(f" SELL {trade_id}: Profit ${profit:.2f}")
                
                # Move USDT to Earn
                usdt_earned = float(order['cost'])
                if usdt_earned >= BinanceConfig.MINIMUM_SUBSCRIPTION['USDT']:
                    self.earn.subscribe('USDT', usdt_earned, TradingConfig.BOT_ID)
                
                # Remove trade
                del self.active_trades[trade_id]
                
            except Exception as e:
                print(f"Failed to sell {trade_id}: {e}")
        
        if total_profit > 0:
            self.save_trades()
            print(f" Total profit from batch: ${total_profit:.2f}")
        
        return total_profit