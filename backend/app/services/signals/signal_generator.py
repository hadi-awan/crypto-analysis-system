# app/services/signals/signal_generator.py
from dataclasses import dataclass
from enum import Enum
import pandas as pd
from typing import List, Callable, Optional

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
            'RSI': self._check_rsi,
            'MACD': self._check_macd,
            'BB': self._check_bollinger_bands
        }

    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """Generate signals based on all available strategies"""
        signals = []
        for indicator, strategy in self.strategies.items():
            if signal := strategy(data):
                signals.append(signal)
        return signals

    def _check_rsi(self, data: pd.DataFrame) -> Optional[Signal]:
        """Generate signals based on RSI"""
        rsi = data['rsi'].iloc[-1]
        timestamp = data['timestamp'].iloc[-1]

        if rsi >= 70:
            strength = min((rsi - 70) / 30, 1)  # Scale strength
            return Signal(
                type=SignalType.SELL,
                indicator="RSI",
                strength=strength,
                message=f"RSI Overbought: {rsi:.2f}",
                timestamp=timestamp
            )
        elif rsi <= 30:
            strength = min((30 - rsi) / 30, 1)
            return Signal(
                type=SignalType.BUY,
                indicator="RSI",
                strength=strength,
                message=f"RSI Oversold: {rsi:.2f}",
                timestamp=timestamp
            )
        return None

    def _check_macd(self, data: pd.DataFrame) -> Optional[Signal]:
        """Generate signals based on MACD crossover"""
        macd = data['macd'].iloc[-1]
        signal = data['macd_signal'].iloc[-1]
        timestamp = data['timestamp'].iloc[-1]

        if macd > signal:
            strength = min((macd - signal) / signal * 100, 1)
            return Signal(
                type=SignalType.BUY,
                indicator="MACD",
                strength=strength,
                message=f"MACD Bullish Crossover",
                timestamp=timestamp
            )
        elif macd < signal:
            strength = min((signal - macd) / signal * 100, 1)
            return Signal(
                type=SignalType.SELL,
                indicator="MACD",
                strength=strength,
                message=f"MACD Bearish Crossover",
                timestamp=timestamp
            )
        return None

    def _check_bollinger_bands(self, data: pd.DataFrame) -> Optional[Signal]:
        """Generate signals based on Bollinger Bands"""
        close = data['close'].iloc[-1]
        upper = data['upper_band'].iloc[-1]
        lower = data['lower_band'].iloc[-1]
        timestamp = data['timestamp'].iloc[-1]

        if close < lower:
            strength = min((lower - close) / (lower * 0.02), 1)  # Scale based on 2% band
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