import pandas as pd
import numpy as np
from typing import Tuple, Dict

class TechnicalAnalyzer:
    def __init__(self, data: pd.DataFrame):
        self.data = data.copy()
        self.validate_data()

    def validate_data(self):
        required_columns = ['timestamp', 'close']
        if not all(col in self.data.columns for col in required_columns):
            raise ValueError(f"Data must contain columns: {required_columns}")

    def calculate_sma(self, period: int = 20, column: str = 'close') -> pd.Series:
        """Calculate Simple Moving Average"""
        return self.data[column].rolling(window=period).mean()

    def calculate_ema(self, period: int = 20, column: str = 'close') -> pd.Series:
        """Calculate Exponential Moving Average"""
        return self.data[column].ewm(span=period, adjust=False).mean()

    def calculate_rsi(self, period: int = 14, column: str = 'close') -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = self.data[column].diff()
        
        # Separate gains and losses
        gain = delta.copy()
        loss = delta.copy()
        gain[gain < 0] = 0
        loss[loss > 0] = 0
        loss = abs(loss)
        
        # Calculate average gain and loss
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        # Handle edge cases
        rsi = rsi.fillna(50)  # Fill initial NaN with neutral RSI
        rsi = rsi.clip(0, 100)  # Ensure RSI stays within [0, 100]
        
        return rsi

    def calculate_macd(self, 
                      fast_period: int = 12, 
                      slow_period: int = 26, 
                      signal_period: int = 9,
                      column: str = 'close') -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate MACD, Signal line, and Histogram"""
        fast_ema = self.calculate_ema(fast_period, column)
        slow_ema = self.calculate_ema(slow_period, column)
        
        macd = fast_ema - slow_ema
        signal = macd.ewm(span=signal_period, adjust=False).mean()
        hist = macd - signal
        
        return macd, signal, hist

    def calculate_bollinger_bands(self, 
                                period: int = 20, 
                                std_dev: float = 2.0,
                                column: str = 'close') -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate Bollinger Bands"""
        # Calculate middle band (SMA)
        middle = self.calculate_sma(period, column)

        # Calculate standard deviation
        std = self.data[column].rolling(window=period).std()

        # Calculate bands
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)

        # Fill NaN values to ensure proper comparison
        middle = middle.fillna(self.data[column])
        upper = upper.fillna(middle + std_dev)
        lower = lower.fillna(middle - std_dev)

        # Force the band order
        upper = pd.Series(np.maximum(upper, middle), index=self.data.index)
        lower = pd.Series(np.minimum(lower, middle), index=self.data.index)

        return upper, middle, lower

    def calculate_atr(self, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        high = self.data['high']
        low = self.data['low']
        close = self.data['close'].shift(1)
        
        # Calculate True Range
        tr1 = abs(high - low)
        tr2 = abs(high - close)
        tr3 = abs(low - close)
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Calculate ATR
        atr = tr.rolling(window=period).mean()
        
        # Fill NaN values with the first valid TR value
        atr = atr.fillna(tr)
        
        # Ensure non-negative values
        return atr.clip(lower=0)

    def calculate_volatility(self, period: int = 20, column: str = 'close') -> pd.Series:
        """Calculate Historical Volatility"""
        # Calculate log returns
        log_return = np.log(self.data[column] / self.data[column].shift(1))
        
        # Calculate volatility (annualized for hourly data)
        volatility = log_return.rolling(window=period).std() * np.sqrt(252 * 24)
        
        # Handle NaN values and ensure non-negative volatility
        volatility = volatility.fillna(0)
        return volatility.clip(lower=0)
    
    def calculate_stochastic(self, period: int = 14, smooth_k: int = 3, smooth_d: int = 3) -> Tuple[pd.Series, pd.Series]:
        """
        Calculate Stochastic Oscillator
        Returns: %K and %D lines
        """
        # Get min and max
        low_min = self.data['low'].rolling(window=period).min()
        high_max = self.data['high'].rolling(window=period).max()
        
        # Calculate raw %K
        k_raw = 100 * (self.data['close'] - low_min) / (high_max - low_min)
        
        # Calculate final %K with smoothing
        k = k_raw.rolling(window=smooth_k, min_periods=smooth_k).mean()
        
        # Calculate %D with smoothing
        d = k.rolling(window=smooth_d, min_periods=smooth_d).mean()
        
        # Handle edge cases
        k = k.replace([np.inf, -np.inf], np.nan).fillna(50)
        d = d.replace([np.inf, -np.inf], np.nan).fillna(50)
        
        # Set initial values to NaN based on required lookback period
        k[:period-1] = np.nan
        d[:period-1] = np.nan
        
        return k.clip(0, 100), d.clip(0, 100)

    def calculate_fibonacci_retracements(self, period=20):
        if len(self.data) < period:
            raise ValueError("Not enough data for the specified period.")

        first_price = self.data['close'].iloc[-period]  # Use iloc for safe indexing
        last_price = self.data['close'].iloc[-1]
        
        # Calculate retracement levels
        difference = last_price - first_price
        retracements = {
            '0.0%': last_price,
            '23.6%': last_price - 0.236 * difference,
            '38.2%': last_price - 0.382 * difference,
            '50.0%': last_price - 0.5 * difference,
            '61.8%': last_price - 0.618 * difference,
            '100.0%': first_price
        }
        return retracements

    def calculate_obv(self) -> pd.Series:
        """Calculate On-Balance Volume"""
        close = self.data['close']
        volume = self.data['volume']
        
        # Calculate price changes
        price_change = close.diff() 
        
        # Initialize OBV
        obv = pd.Series(0, index=self.data.index)
        
        # Calculate OBV
        obv[price_change > 0] = volume[price_change > 0]
        obv[price_change < 0] = -volume[price_change < 0]
        
        return obv.cumsum()