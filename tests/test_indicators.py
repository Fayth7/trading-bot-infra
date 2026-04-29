"""
Unit tests for technical indicators
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from bot.indicators import TechnicalIndicators


class TestTechnicalIndicators(unittest.TestCase):
    
    def setUp(self):
        self.mock_exchange = Mock()
        self.indicators = TechnicalIndicators(self.mock_exchange)
    
    @patch('bot.indicators.talib')
    def test_get_indicators_handles_error(self, mock_talib):
        """Test that get_enhanced_indicators handles API errors"""
        self.mock_exchange.fetch_ohlcv.side_effect = Exception("API Error")
        
        result = self.indicators.get_enhanced_indicators()
        
        self.assertIsNone(result)
    
    def test_calculate_buy_score_returns_valid_score(self):
        """Test buy score calculation returns expected range"""
        mock_indicators = {
            'rsi_5m': 25,
            'rsi_15m': 28,
            'current_price': 2000,
            'recent_low': 1950,
            'ema_9': 2000,
            'ema_21': 2010,
            'macd_line': -5,
            'macd_signal': -3,
            'current_volume': 1000,
            'avg_volume': 1200
        }
        
        score, confidence = self.indicators.calculate_buy_score(mock_indicators)
        
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 10)
        self.assertIn(confidence, ['HIGH', 'MODERATE', 'LOW', 'NO_SIGNAL', 'RSI_TOO_HIGH'])


if __name__ == '__main__':
    unittest.main()