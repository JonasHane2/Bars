"""
Implementation of Bars and Imbalance Bars sampling scheme for financial time series. 
"""
import pandas as pd
import numpy as np
from scipy.optimize import minimize_scalar
bar_types = ["tick", "volume", "dollar"]

class Bars():
    """
    Implementation of the Bars sampling scheme for financial time series.

    Attributes:
        bar_type (str): Type of bars to sample. One of {'tick', 'volume', 'dollar'}.
        imbalance (bool): True for imbalance bars, False otherwise.
        avg_bars_per_day (float): Target number of samples per day (calibrated on historical trades).
        beta (int): Lookback window (number of trades) for calibrating the threshold.
        theta (float): Current value of theta.
        past_beta_trades (pd.DataFrame): History of past beta trades.
        threshold (float): Current threshold for theta breaches.

    Methods:
        set_threshold(trades: pd.DataFrame) -> float:
            Returns an estimate for the threshold to achieve the desired bar sampling frequency.

        get_inc(trades: pd.DataFrame) -> pd.Series:
            Returns the multiplication factor depending on the bar type.

        tick_rule(trade: float) -> float:
            Returns the sign of the price change or the previous sign if the price is unchanged.

        register_trade(trade: pd.Series) -> bool:
            Registers a trade and checks whether theta breaches the threshold.

        register_trade_history(trade, imbalance) -> None:
            Registers the trade to the past history of trades and ensures the length of the history never exceeds beta.

        get_all_bar_ids(trades: pd.DataFrame) -> list:
            Returns the indices of trades when the threshold is breached.
    """

    def __init__(self, bar_type="tick", imbalance_sign=False, avg_bars_per_day=100, beta=1000) -> None:
        """
        Initializes a Bars object with the specified settings.

        Args:
            bar_type (str): Type of bars to sample. One of {'tick', 'volume', 'dollar'}.
            imbalance (bool): True for imbalance bars, False otherwise.
            avg_bars_per_day (float): Target number of samples per day.
            beta (int): Lookback window for calibrating the threshold.
        """
        if bar_type not in bar_types:
            raise ValueError("Invalid imbalance type %s. Expected one of: %s" % (bar_type, bar_types))        
        self.imbalance_sign = imbalance_sign
        self.avg_bars_per_day = avg_bars_per_day
        self.theta = 0
        self.bar_type = bar_type
        self.beta = beta
        self.past_beta_trades = pd.DataFrame(columns=['Volume', 'Price', 'Imbalance'])
        self.threshold = self.set_threshold(self.past_beta_trades)

    def set_threshold(self, trades: pd.DataFrame) -> float:
        """
        Returns an estimate for threshold to get a target average number of samples 
        per day based on the trades.

        Args: 
            trades (dataframe): prices and volumes for trades
            avg_bars_per_day (integer): the target number of samples per day. 
        Returns: 
            (float): the threshold to achieve the desired bar sampling frequency. 
        """
        if len(trades) == 0:
            return 1
        
        series = self.get_inc(trades)
        result = minimize_scalar(lambda threshold: abs(calculate_avg_threshold_breaches_per_day(threshold, series) - self.avg_bars_per_day),
                                    bounds=(0, series.cumsum().abs().max()), method='bounded', options={'disp': False})

        return result.x

    def get_inc(self, trades: pd.DataFrame) -> float:
        """
        Args: 
            trades (pd.Series): information about one or more ticks
        Returns: 
            (float): the multiplication factor depending on what bar type we use.
        """
        if self.bar_type == "tick":
            series = trades['Imbalance']
        elif self.bar_type == "volume":
            series = trades['Volume']*trades['Imbalance']
        else:
            series = trades['Volume']*trades['Price']*trades['Imbalance']
        return series

    def tick_rule(self, trade: float) -> float:
        """ Returns the sign of the price change, or the previous sign if the price is unchanged. 
        Is only relevant for imbalance bars, always returns 1 for normal bars. 
        
        Returns:
            (int): sign of imbalance (price change),
        """
        if not self.imbalance_sign:
            return 1
        
        if len(self.past_beta_trades) == 0:
            return 0
        
        delta = trade['Price'] - self.past_beta_trades.iloc[-1]['Price']
        return np.sign(delta) if delta != 0 else self.past_beta_trades.iloc[-1, self.past_beta_trades.columns.get_loc('Imbalance')]
    
    def register_trade(self, trade: pd.Series) -> bool:
        """
        Registers a trade and checks whether theta breaches the threshold.

        Args:
            trade (pd.Series): information about a single tick
        Returns:
            (bool): True if theta breaches threshold, 
                                     otherwise false
        """
        imbalance = self.tick_rule(trade)
        self.register_trade_history(trade, imbalance)
        self.theta += self.get_inc(self.past_beta_trades.iloc[-1])
        
        if abs(self.theta) > self.threshold:
            self.theta = 0
            self.threshold = self.set_threshold(self.past_beta_trades)
            return True 
        
        return False 

    def register_trade_history(self, trade, imbalance) -> None:
        """
        This function registers the trade to the past history of trades
        and makes shure that the length of the history never exceeds beta.

        Args:
            trade (pd.Series): information about a trade to be registered
            imbalance (int): sign of imbalance (-1/+1)
        """
        self.past_beta_trades = pd.concat([self.past_beta_trades, trade.to_frame().T])
        self.past_beta_trades.iloc[-1, self.past_beta_trades.columns.get_loc('Imbalance')] = imbalance
        if len(self.past_beta_trades) > self.beta:
            self.past_beta_trades = self.past_beta_trades.iloc[1:]

    def get_all_bar_ids(self, trades: pd.DataFrame) -> list:
        """
        Args: 
            trades (DataFrame): list of all trades
        Returns: 
            idx (list): indices of when the threshold is breached
        """
        idx =[]
        for index, trade in trades.iterrows():
            if self.register_trade(trade):
                idx.append(index)
        return idx


def calculate_avg_threshold_breaches_per_day(threshold: float, series: pd.Series) -> float:
    """
    Args: 
        threshold (float): the threshold for theta breaches
        series (pd.Series): the trade (tick/volume/dollar) imbalances
    Returns: 
        (float): the average number of threshold breaches per day on the imbalances
                 from 'series' if the threshold was set to 'threshold' 
    """
    threshold_breaches, theta_sum = 0, 0
    unique_days = series.index.nunique()
    
    for value in series:
        theta_sum+=value
        if abs(theta_sum) >= threshold:
            threshold_breaches += 1
            theta_sum = 0

    return threshold_breaches / unique_days
