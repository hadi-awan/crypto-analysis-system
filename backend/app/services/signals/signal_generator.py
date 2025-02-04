
# app/services/signals/signal_generator.py
from dataclasses import dataclass
from enum import Enum
import pandas as pd
from typing import List, Callable, Optional
from app.validation.price_validators import PriceDataValidator

class SignalType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    NEUTRAL = "NEUTRAL"

@dataclass
class Signal:
    type: SignalType
    indicator: str
    strength: float
    message: str
    timestamp: pd.Timestamp

class SignalGenerator:
    def __init__(self):
        self.strategies = {
            'RSI': (self._check_rsi, ['rsi']),
            'MACD': (self._check_macd, ['macd', 'macd_signal', 'close']),
            'BB': (self._check_bollinger_bands, ['bb_upper', 'bb_lower', 'close']),
            'STOCH': (self._check_stochastic, ['stoch_k', 'stoch_d'])
        }

    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """Generate signals based on available indicators"""
        signals = []
        for indicator, (strategy, required_columns) in self.strategies.items():
            # Only run strategy if all required columns are present
            if all(col in data.columns for col in required_columns):
                if signal := strategy(data):
                    signals.append(signal)
        return signals

    def _check_rsi(self, data: pd.DataFrame) -> Optional[Signal]:
        """Generate signals based on RSI"""
        rsi = data['rsi'].iloc[-1]
        timestamp = data['timestamp'].iloc[-1]

        if rsi >= 70:
            # Adjust strength calculation for overbought
            # Now RSI of 85+ will give strength > 0.8
            strength = min((rsi - 70) / 15, 1)
            return Signal(
                type=SignalType.SELL,
                indicator="RSI",
                strength=strength,
                message=f"RSI Overbought: {rsi:.2f}",
                timestamp=timestamp
            )
        elif rsi <= 30:
            # Adjust strength calculation for oversold
            # RSI of 15 or lower will give strength > 0.8
            strength = min((30 - rsi) / 15, 1)
            return Signal(
                type=SignalType.BUY,
                indicator="RSI",
                strength=strength,
                message=f"RSI Oversold: {rsi:.2f}",
                timestamp=timestamp
            )
        return None

    def _check_macd(self, data: pd.DataFrame) -> Optional[Signal]:
        """Generate signals based on MACD crossover and zero line."""
        macd = data['macd'].iloc[-1]
        signal = data['macd_signal'].iloc[-1]
        timestamp = data['timestamp'].iloc[-1]
        price = data['close'].iloc[-1]  # Get current price for normalization

        # MACD Bullish Crossover
        if macd > signal:
            # Calculate strength based on the difference relative to price
            strength = min(abs(macd - signal) / (price * 0.001), 1.0)  # Scale by 0.1% of price
            return Signal(
                type=SignalType.BUY,
                indicator="MACD",
                strength=strength,
                message=f"MACD Bullish Crossover ({strength*100:.2f}% strength)",
                timestamp=timestamp
            )

        # MACD Bearish Crossover
        elif macd < signal:
            # Calculate strength based on the difference relative to price
            strength = min(abs(macd - signal) / (price * 0.001), 1.0)  # Scale by 0.1% of price
            return Signal(
                type=SignalType.SELL,
                indicator="MACD",
                strength=strength,
                message=f"MACD Bearish Crossover ({strength*100:.2f}% strength)",
                timestamp=timestamp
            )

        return None

    def _check_bollinger_bands(self, data: pd.DataFrame) -> Optional[Signal]:
        """Generate signals based on Bollinger Bands"""
        close = data['close'].iloc[-1]
        upper = data['bb_upper'].iloc[-1]  # Changed from upper_band to bb_upper
        lower = data['bb_lower'].iloc[-1]  # Changed from lower_band to bb_lower
        timestamp = data['timestamp'].iloc[-1]

        if close < lower:
            strength = min((lower - close) / (lower * 0.02), 1)  # Scale strength
            return Signal(
                type=SignalType.BUY,
                indicator="BB",
                strength=strength,
                message=f"Price below Lower Bollinger Band",
                timestamp=timestamp
            )
        elif close > upper:
            strength = min((close - upper) / (upper * 0.02), 1)
            return Signal(
                type=SignalType.SELL,
                indicator="BB",
                strength=strength,
                message=f"Price above Upper Bollinger Band",
                timestamp=timestamp
            )
        return None
    
    def _check_stochastic(self, data: pd.DataFrame) -> Optional[Signal]:
        """Generate signals based on Stochastic Oscillator"""
        k = data['stoch_k'].iloc[-1]
        d = data['stoch_d'].iloc[-1]
        timestamp = data['timestamp'].iloc[-1]

        # Oversold conditions (both K and D below 20)
        if k < 20 and d < 20:
            # Calculate strength based on how oversold it is
            strength = (20 - max(k, d)) / 20  # More oversold = higher strength
            return Signal(
                type=SignalType.BUY,
                indicator="STOCH",
                strength=strength,
                message=f"Stochastic Oversold: %K={k:.1f}, %D={d:.1f}",
                timestamp=timestamp
            )
            
        # Overbought conditions (both K and D above 80)
        elif k > 80 and d > 80:
            # Calculate strength based on how overbought it is
            strength = (min(k, d) - 80) / 20  # More overbought = higher strength
            return Signal(
                type=SignalType.SELL,
                indicator="STOCH",
                strength=strength,
                message=f"Stochastic Overbought: %K={k:.1f}, %D={d:.1f}",
                timestamp=timestamp
            )
            
        return None