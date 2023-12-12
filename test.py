import unittest
import pandas as pd
from bars import Bars
from datetime import datetime

class TestBars(unittest.TestCase):

    def setUp(self):
        # Initialize a Bars object with some sample data
        self.trades_data = {
            'Timestamp': [datetime(2023, 1, 1, 10, 0, 0),
                            datetime(2023, 1, 1, 10, 1, 0),
                            datetime(2023, 1, 1, 10, 2, 0),
                            datetime(2023, 1, 1, 10, 3, 0),
                            datetime(2023, 1, 1, 10, 4, 0)],
            'Volume': [100, 150, 50, 120, 80],
            'Price': [50, 51, 50.5, 49.8, 47.6],
            'Imbalance': [1, -1, 1, -1, -1]
        }
        self.trades_df = pd.DataFrame(self.trades_data)
        self.trades_df.set_index('Timestamp', inplace=True)
        self.bars = Bars(bar_type="tick", imbalance_sign=False, avg_bars_per_day=3, beta=3)

    def test_initialization(self):
        self.assertEqual(self.bars.bar_type, "tick")
        self.assertEqual(self.bars.avg_bars_per_day, 3)
        self.assertEqual(self.bars.beta, 3)
        self.assertEqual(self.bars.theta, 0)
        self.assertEqual(self.bars.threshold, 0)

    def test_set_threshold(self):
        # Test set_threshold method with an empty DataFrame
        threshold = self.bars.set_threshold(pd.DataFrame())
        self.assertEqual(threshold, 0)

        # Test set_threshold method with some trades data
        threshold = self.bars.set_threshold(self.trades_df)
        self.assertTrue(isinstance(threshold, float))

    def test_get_inc(self):
        # Test get_inc method with different bar types
        self.assertTrue(self.bars.get_inc(self.trades_df).equals(self.trades_df['Imbalance']))

        self.bars.bar_type = "volume"
        self.assertTrue(self.bars.get_inc(self.trades_df).equals(self.trades_df['Volume'] * self.trades_df['Imbalance']))

        self.bars.bar_type = "dollar"
        self.assertTrue(self.bars.get_inc(self.trades_df).equals(self.trades_df['Volume'] * self.trades_df['Price'] * self.trades_df['Imbalance']))

    def test_tick_rule(self):
        # Test tick_rule method with different scenarios
        self.bars.imbalance_sign = False
        self.assertEqual(self.bars.tick_rule({'Price': 50}), 1)
        self.assertEqual(self.bars.tick_rule({'Price': 45}), 1)
        self.assertEqual(self.bars.tick_rule({'Price': 55}), 1)

        self.bars.imbalance_sign = True
        self.assertEqual(self.bars.tick_rule({'Price': 50}), 0)

        self.bars.past_beta_trades = pd.DataFrame({'Price': [49.8], 'Imbalance': [-1]})
        self.assertEqual(self.bars.tick_rule({'Price': 49.8}), -1)
        self.assertEqual(self.bars.tick_rule({'Price': 45}), -1)
        self.assertEqual(self.bars.tick_rule({'Price': 50}), 1)

    def test_register_trade(self):
        # Test register_trade method with different scenarios
        trade = pd.Series({'Volume': 100, 'Price': 50.5, 'Imbalance': 1})

        # First trade, theta doesn't breach threshold
        self.bars.threshold = 1
        self.assertFalse(self.bars.register_trade(trade))

        # Second trade, theta breaches threshold
        self.bars.threshold = 0
        self.assertTrue(self.bars.register_trade(trade))

    def test_register_trade_history(self):
        # Test register_trade_history method
        trade = pd.Series({'Volume': 100, 'Price': 50.5, 'Imbalance': 1})
        imbalance = self.bars.tick_rule(trade)

        # Register the trade in the history
        self.bars.register_trade_history(trade, imbalance)
        self.assertEqual(len(self.bars.past_beta_trades), 1)

        # Register more trades to exceed beta
        for _ in range(5):
            self.bars.register_trade_history(trade, imbalance)

        self.assertEqual(len(self.bars.past_beta_trades), self.bars.beta)

    def test_get_all_bar_ids(self):
        # Test get_all_bar_ids method with different scenarios
        bar_ids = self.bars.get_all_bar_ids(self.trades_df)
        expected_indices = [self.trades_df.index[i] for i in [0,1,2]]
        self.assertEqual(bar_ids, expected_indices)

        self.bars = Bars(bar_type="volume", imbalance_sign=False, avg_bars_per_day=3, beta=3)
        bar_ids = self.bars.get_all_bar_ids(self.trades_df)
        expected_indices = [self.trades_df.index[i] for i in [0,1,3,4]]
        self.assertEqual(bar_ids, expected_indices)

        self.bars = Bars(bar_type="dollar", imbalance_sign=False, avg_bars_per_day=3, beta=3)
        bar_ids = self.bars.get_all_bar_ids(self.trades_df)
        expected_indices = [self.trades_df.index[i] for i in [0,1,3]]
        self.assertEqual(bar_ids, expected_indices)

if __name__ == '__main__':
    unittest.main()