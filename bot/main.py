"""
ETH/USDT Trading Bot with Auto-Earn
Main entry point
"""

import time
import traceback
import ccxt
from datetime import datetime

from config.settings import (
    TradingConfig, BinanceConfig, EmailConfig, 
    FileConfig, validate_config, init_directories
)
from bot.indicators import TechnicalIndicators
from bot.trading import TradeManager
from bot.monitoring import Monitor
from bot.utils import get_timestamp_eat, ensure_directories


class TradingBot:
    """Main trading bot orchestrator"""
    
    def __init__(self):
        print(" Initializing ETH/USDT Trading Bot...")
        
        # Validate configuration
        validate_config()
        init_directories()
        ensure_directories()
        
        # Initialize exchange
        self.exchange = ccxt.binance({
            'apiKey': BinanceConfig.API_KEY,
            'secret': BinanceConfig.SECRET_KEY,
            'enableRateLimit': True,
            'options': {
                'adjustForTimeDifference': True,
                'recvWindow': 10000,
            }
        })
        
        # Initialize components
        self.indicators = TechnicalIndicators(self.exchange)
        self.trades = TradeManager(self.exchange)
        self.monitor = Monitor(self.exchange, self.trades)
        
        # Trailing buy state
        self.trailing_buy = {
            'active': False,
            'lowest_price': 0,
            'start_time': 0
        }
        
        self.cycle_count = 0
        self.running = True
    
    def run(self):
        """Main trading loop"""
        print("="*50)
        print(f"Bot Started: {get_timestamp_eat().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Trading Pair: {TradingConfig.TRADING_PAIR}")
        print(f"Check Interval: {TradingConfig.CHECK_INTERVAL}s")
        print(f"Max Trades: {TradingConfig.MAX_ACTIVE_TRADES}")
        print("="*50)
        
        try:
            while self.running:
                cycle_start = time.time()
                self.cycle_count += 1
                
                try:
                    # Get current price
                    ticker = self.exchange.fetch_ticker(TradingConfig.TRADING_PAIR)
                    current_price = ticker['last']
                    
                    # 1. Check sell conditions
                    trades_to_sell, price = self.trades.check_sell_conditions()
                    if trades_to_sell:
                        self.trades.execute_sell(trades_to_sell, price)
                    
                    # 2. Check buy conditions
                    if self.trades.can_buy():
                        indicators = self.indicators.get_enhanced_indicators()
                        
                        if indicators:
                            score, confidence = self.indicators.calculate_buy_score(indicators)
                            
                            if score >= 6:  # Buy threshold
                                self._handle_buy_signal(score, confidence, indicators)
                    
                    # 3. Health checks (periodic)
                    if self.cycle_count % 10 == 0:
                        self.monitor.health_check()
                    
                    if self.cycle_count % 20 == 0:
                        self.monitor.send_status_report()
                    
                    # 4. Weekly report
                    if self.cycle_count % 20160 == 0:  # ~1 week at 30s intervals
                        self.monitor.send_weekly_report()
                    
                    # Sleep
                    elapsed = time.time() - cycle_start
                    sleep_time = max(1, TradingConfig.CHECK_INTERVAL - elapsed)
                    time.sleep(sleep_time)
                    
                except KeyboardInterrupt:
                    self.shutdown()
                    break
                except Exception as e:
                    print(f" Cycle error: {e}")
                    traceback.print_exc()
                    time.sleep(30)
                    
        except Exception as e:
            print(f" Fatal error: {e}")
            traceback.print_exc()
        finally:
            self.shutdown()
    
    def _handle_buy_signal(self, score, confidence, indicators):
        """Handle buy signal with trailing logic"""
        current_price = indicators['current_price']
        rsi = indicators['rsi_5m']
        
        print(f"Buy Signal: Score={score:.1f}, Confidence={confidence}")
        
        # Trailing buy logic
        if not self.trailing_buy['active']:
            print(" Activating trailing buy mode")
            self.trailing_buy = {
                'active': True,
                'lowest_price': current_price,
                'start_time': time.time()
            }
            return
        
        # Update lowest price
        self.trailing_buy['lowest_price'] = min(
            self.trailing_buy['lowest_price'],
            current_price
        )
        
        # Check if price bounced enough
        target_price = self.trailing_buy['lowest_price'] * 1.001  # 0.1% bounce
        timeout = time.time() - self.trailing_buy['start_time'] > 3600  # 1 hour
        
        if current_price >= target_price or timeout:
            print(" Executing buy order")
            self.trades.execute_buy(score, confidence, rsi)
            self.trailing_buy['active'] = False
        else:
            print(f" Trailing: Low=${self.trailing_buy['lowest_price']:.2f}, Target=${target_price:.2f}")
    
    def shutdown(self):
        """Graceful shutdown"""
        print("\n Shutting down bot...")
        self.running = False
        self.trades.save_trades()
        print("Trades saved. Goodbye!")


if __name__ == "__main__":
    bot = TradingBot()
    bot.run()