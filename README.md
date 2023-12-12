# Financial Bars and Imbalance Bars Sampling Scheme

Implementation of the Bars and Imbalance Bars sampling scheme for financial time series data defined in the book Advances in Financial Machine Learning by Marcos Lopez de Prado. 

Imbalance bars samples bars as a function of transactions/transaction volume/dollar transaction volume which exhibits better statistical properties like closer to Gaussian and IID returns, and less autocorrelation and heteroskedasticity. 

## Bars Class

The `Bars` class is designed to sample financial time series data based on different bar types, including 'tick', 'volume', and 'dollar'. Additionally, it supports the sampling of imbalance bars, providing flexibility for different analytical needs.

### Attributes

- `bar_type (str)`: Type of bars to sample. Options: {'tick', 'volume', 'dollar'}.
- `imbalance_sign (bool)`: True for imbalance bars, False otherwise.
- `avg_bars_per_day (float)`: Target number of samples per day.
- `beta (int)`: Lookback window for calibrating the threshold.
- `theta (float)`: Current value of theta.
- `past_beta_trades (pd.DataFrame)`: History of past beta trades.
- `threshold (float)`: Current threshold for theta breaches.

### Methods

1. **`set_threshold(trades: pd.DataFrame) -> float`**
   - Returns an estimate for the threshold to achieve the desired bar sampling frequency.

2. **`get_inc(trades: pd.DataFrame) -> pd.Series`**
   - Returns the multiplication factor depending on the bar type.

3. **`tick_rule(trade: float) -> float`**
   - Returns the sign of the price change or the previous sign if the price is unchanged. Relevant for imbalance bars; always returns 1 for normal bars.

4. **`register_trade(trade: pd.Series) -> bool`**
   - Registers a trade and checks whether theta breaches the threshold.

5. **`register_trade_history(trade, imbalance) -> None`**
   - Registers the trade to the past history of trades and ensures the length of the history never exceeds beta.

6. **`get_all_bar_ids(trades: pd.DataFrame) -> list`**
   - Returns the indices of trades when the threshold is breached.

### Usage Example

```python
from financial_bars import Bars

# Create a Bars object
tick_bars = Bars(bar_type='tick', imbalance_sign=False, avg_bars_per_day=100)

# Sample bars from financial time series data
# Ensure data is a DataFrame with columns ['Price'] and ['Volume'] indexed in timestamps
data = ...

# Get indices when the threshold is breached
bar_ids = tick_bars.get_all_bar_ids(data)
```

## Testing

To ensure the correctness of the implemented Bars and Imbalance Bars sampling scheme, a set of unit tests is provided. These tests cover various aspects of the `Bars` class functionality.

### Running Tests

To run the tests, execute the following command in your terminal:

```bash
python test.py