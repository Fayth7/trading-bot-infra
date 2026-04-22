"""
Technical indicators using TA-Lib
"""

import numpy as np
import talib
import ccxt
from config.settings import TradingConfig


class TechnicalIndicators:
    """Get trading signals using TA-Lib"""
    
    def __init__(self, exchange):
        self.exchange = exchange
        self.pair = TradingConfig.TRADING_PAIR
    
    def get_enhanced_indicators(self):
        """
        Get multiple indicators for better buy signal confirmation
        Returns dict with RSI, EMA, MACD, volume analysis
        """
        try:
            # Get multiple timeframes
            ohlcv_5m = self.exchange.fetch_ohlcv(self.pair, timeframe='5m', limit=50)
            ohlcv_15m = self.exchange.fetch_ohlcv(self.pair, timeframe='15m', limit=30)
            
            # Convert to numpy arrays for TA-Lib
            close_5m = np.array([x[4] for x in ohlcv_5m], dtype=float)
            close_15m = np.array([x[4] for x in ohlcv_15m], dtype=float)
            high_5m = np.array([x[2] for x in ohlcv_5m], dtype=float)
            low_5m = np.array([x[3] for x in ohlcv_5m], dtype=float)
            volume_5m = np.array([x[5] for x in ohlcv_5m], dtype=float)
            
            # Core indicators using TA-Lib
            rsi_5m = talib.RSI(close_5m, timeperiod=14)[-1]
            rsi_15m = talib.RSI(close_15m, timeperiod=14)[-1]
            
            # EMAs for trend
            ema_9 = talib.EMA(close_5m, timeperiod=9)[-1]
            ema_21 = talib.EMA(close_5m, timeperiod=21)[-1]
            
            # MACD for momentum
            macd_line, macd_signal, macd_hist = talib.MACD(
                close_5m, fastperiod=12, slowperiod=26, signalperiod=9
            )
            
            # Volume analysis (simple moving average)
            avg_volume = np.mean(volume_5m[-10:]) if len(volume_5m) >= 10 else volume_5m[-1]
            current_volume = volume_5m[-1]
            
            # Price levels
            current_price = close_5m[-1]
            recent_high = np.max(high_5m[-12:]) if len(high_5m) >= 12 else high_5m[-1]
            recent_low = np.min(low_5m[-8:]) if len(low_5m) >= 8 else low_5m[-1]
            
            return {
                'rsi_5m': float(rsi_5m) if not np.isnan(rsi_5m) else 50,
                'rsi_15m': float(rsi_15m) if not np.isnan(rsi_15m) else 50,
                'ema_9': float(ema_9),
                'ema_21': float(ema_21),
                'macd_line': float(macd_line[-1]) if not np.isnan(macd_line[-1]) else 0,
                'macd_signal': float(macd_signal[-1]) if not np.isnan(macd_signal[-1]) else 0,
                'current_price': float(current_price),
                'recent_high': float(recent_high),
                'recent_low': float(recent_low),
                'avg_volume': float(avg_volume),
                'current_volume': float(current_volume)
            }
            
        except Exception as e:
            print(f"Error getting indicators: {e}")
            return None
    
    def calculate_buy_score(self, indicators):
        """
        Calculate buy signal score based on multiple factors
        Returns score (0-10) and confidence level
        """
        if not indicators:
            return 0, "NO_SIGNAL"
        
        rsi_5m = indicators['rsi_5m']
        rsi_15m = indicators['rsi_15m']
        current_price = indicators['current_price']
        recent_low = indicators['recent_low']
        ema_9 = indicators['ema_9']
        ema_21 = indicators['ema_21']
        macd_line = indicators['macd_line']
        macd_signal = indicators['macd_signal']
        current_volume = indicators['current_volume']
        avg_volume = indicators['avg_volume']
        
        # RSI must be below threshold
        if rsi_5m >= TradingConfig.RSI_BUY_THRESHOLD:
            return 0, "RSI_TOO_HIGH"
        
        # Base score starts at 3 for passing RSI
        score = 3
        max_score = 10
        
        # 1. RSI Strength (extra points for deep oversold)
        if rsi_5m < 25:
            score += 1
        
        # 2. 15-minute confirmation
        if rsi_15m < 30:
            score += 1
        elif rsi_15m < 40:
            score += 0.5
        
        # 3. Proximity to recent low
        distance_from_low = (current_price - recent_low) / recent_low * 100
        if distance_from_low <= 2.0:
            score += 2
        elif distance_from_low <= 4.0:
            score += 1
        
        # 4. Trend conditions
        short_term_bullish = ema_9 > ema_21
        if not short_term_bullish:
            score += 2
        else:
            # Calculate pullback from high
            recent_high = indicators['recent_high']
            pullback = (recent_high - current_price) / recent_high * 100
            if pullback >= 1.5:
                score += 2
            elif pullback >= 0.8:
                score += 1
        
        # 5. MACD momentum
        if macd_line > macd_signal:
            score += 1
        
        # 6. Volume confirmation
        if current_volume >= avg_volume * 0.8:
            score += 1
        elif current_volume >= avg_volume * 0.6:
            score += 0.5
        
        # Determine confidence
        if score >= 7.5:
            confidence = "HIGH"
        elif score >= 6:
            confidence = "MODERATE"
        elif score >= 4:
            confidence = "LOW"
        else:
            confidence = "NO_SIGNAL"
        
        return score, confidence