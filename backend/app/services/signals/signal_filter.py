# app/services/signals/signal_filter.py
from dataclasses import dataclass
from typing import List, Optional, Dict
from .signal_generator import Signal, SignalType
from datetime import datetime

@dataclass
class FilterConfig:
    min_strength: float = 0.3
    required_confirmations: int = 1
    cooldown_period: int = 300  # seconds
    allowed_indicators: Optional[List[str]] = None

class SignalFilter:
    def __init__(self, config: FilterConfig):
        self.config = config
        self.recent_signals: Dict[str, datetime] = {}

    def filter_signal(self, signal: Signal) -> bool:
        """
        Filter signals based on strength, cooldown period, and other criteria
        Returns True if signal should be included, False if filtered out
        """
        # Check signal strength
        if signal.strength < self.config.min_strength:
            return False
            
        # Check if indicator is allowed
        if self.config.allowed_indicators and signal.indicator not in self.config.allowed_indicators:
            return False
            
        # Check cooldown period
        key = f"{signal.indicator}_{signal.type}"  # Using signal.type instead of signal.signal_type
        if key in self.recent_signals:
            last_signal_time = self.recent_signals[key]
            cooldown_delta = timedelta(seconds=self.config.cooldown_period)
            if datetime.now() - last_signal_time < cooldown_delta:
                return False
                
        return True

    def _check_strength(self, signal: Signal) -> bool:
        """Check if signal meets minimum strength requirement"""
        return signal.strength >= self.config.min_strength

    def _check_cooldown(self, signal: Signal) -> bool:
        """Check if enough time has passed since last signal"""
        key = f"{signal.indicator}_{signal.type.value}"
        if key in self.last_signal_time:
            time_diff = (signal.timestamp - self.last_signal_time[key]).total_seconds()
            if time_diff < self.config.cooldown_period:
                return False
        self.last_signal_time[key] = signal.timestamp
        return True

    def _check_indicator_allowed(self, signal: Signal) -> bool:
        """Check if indicator is in allowed list"""
        if self.config.allowed_indicators is None:
            return True
        return signal.indicator in self.config.allowed_indicators

    def _check_confirmations(self, signal: Signal) -> bool:
        """Check if signal has enough confirmations from other indicators"""
        if self.config.required_confirmations <= 1:
            return True

        # Count recent signals in same direction
        recent_count = sum(
            1 for s in self.recent_signals[-5:]  # Look at last 5 signals
            if s.type == signal.type and s.indicator != signal.indicator
        )
        
        return recent_count >= (self.config.required_confirmations - 1)

    def update_recent_signals(self, signal: Signal):
        """Update the record of recent signals"""
        key = f"{signal.indicator}_{signal.type}"  # Using signal.type instead of signal.signal_type
        self.recent_signals[key] = signal.timestamp