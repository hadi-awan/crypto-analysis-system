# app/services/filters/signal_filter.py
from dataclasses import dataclass
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from app.services.signals.signal_generator import Signal, SignalType

@dataclass
class FilterConfig:
   min_strength: float = 0.3  # Minimum signal strength to consider
   required_confirmations: int = 1  # Number of confirmations needed
   cooldown_period: int = 300  # Cooldown in seconds between similar signals
   allowed_indicators: Optional[List[str]] = None  # List of allowed indicators

class SignalFilter:
   def __init__(self, config: FilterConfig):
       self.config = config
       self.last_signal_time: Dict[str, datetime] = {}  # Track last signal times
       self.recent_signals: List[Signal] = []  # Track recent signals for confirmation

   def filter_signal(self, signal: Signal) -> bool:
       """Apply all filters to a signal"""
       if not self._check_strength(signal):
           return False

       if not self._check_cooldown(signal):
           return False

       if not self._check_indicator_allowed(signal):
           return False

       if not self._check_confirmations(signal):
           return False

       return True

   def _check_strength(self, signal: Signal) -> bool:
       """Check if signal meets minimum strength requirement"""
       return signal.strength >= self.config.min_strength

   def _check_cooldown(self, signal: Signal) -> bool:
       """Check if enough time has passed since last similar signal"""
       # Create unique key for signal type + indicator combination
       key = f"{signal.indicator}_{signal.type.value}"
       
       if key in self.last_signal_time:
           time_diff = (signal.timestamp - self.last_signal_time[key]).total_seconds()
           if time_diff < self.config.cooldown_period:
               return False
               
       # Update last signal time
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
           1 for s in self.recent_signals[-10:]  # Look at last 10 signals
           if s.type == signal.type  # Same direction
           and s.indicator != signal.indicator  # Different indicator
           and (signal.timestamp - s.timestamp).total_seconds() <= 300  # Within 5 minutes
       )

       return recent_count >= (self.config.required_confirmations - 1)

   def update_recent_signals(self, signal: Signal):
       """Update the list of recent signals"""
       self.recent_signals.append(signal)
       
       # Keep only last 10 signals
       if len(self.recent_signals) > 10:
           self.recent_signals = self.recent_signals[-10:]

       # Remove signals older than 5 minutes
       current_time = signal.timestamp
       self.recent_signals = [
           s for s in self.recent_signals 
           if (current_time - s.timestamp).total_seconds() <= 300
       ]