"""
Unit tests for trading logic
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from bot.trading import TradeManager


class TestTradeManager(unittest.TestCase):
    
    def setUp(self):
        self.mock_exchange = Mock()
        self.trades = TradeManager(self.mock_exchange)
    
    def test_can_buy_initial_state(self):
        """Test can_buy returns True initially"""
        self.assertTrue(self.trades.can_buy())
    
    def test_can_buy_respects_max_trades(self):
        """Test can_buy returns False when max trades reached"""
        # Fill with max trades
        for i in range(4):
            self.trades.active_trades[f"TRADE_{i}"] = {'buy_price': 2000}
        
        self.assertFalse(self.trades.can_buy())
    
    @patch('bot.trading.TradingConfig.TRADE_COOLDOWN', 60)
    def test_can_buy_respects_cooldown(self):
        """Test can_buy respects cooldown period"""
        self.trades.last_buy_time = 9999999999  # Future time
        
        self.assertFalse(self.trades.can_buy())


if __name__ == '__main__':
    unittest.main()