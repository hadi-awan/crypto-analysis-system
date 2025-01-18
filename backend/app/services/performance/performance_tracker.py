# app/services/performance/performance_tracker.py
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum
import pandas as pd
import logging

class SignalOutcome(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    PENDING = "pending"
    EXPIRED = "expired"

@dataclass
class PerformanceMetrics:
    total_signals: int
    success_count: int
    failure_count: int
    win_rate: float
    avg_return: float
    avg_holding_time: timedelta
    profit_factor: float
    accuracy_by_indicator: Dict[str, float]
    accuracy_by_type: Dict[str, float]

@dataclass
class SignalResult:
    signal_id: str
    type: str  # BUY or SELL
    indicator: str
    entry_price: float
    entry_time: datetime
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    outcome: SignalOutcome = SignalOutcome.PENDING
    return_pct: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None

class PerformanceTracker:
    def __init__(self):
        self.active_signals: Dict[str, SignalResult] = {}
        self.completed_signals: List[SignalResult] = []
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.signal_timeout = timedelta(hours=24)  # Max time to wait for signal completion
        self.min_profit_threshold = 0.5  # Minimum % profit to consider success
        self.max_loss_threshold = -1.0  # Maximum % loss before considering failure
        
    def add_signal(self, signal_id: str, signal_type: str, indicator: str, 
                   entry_price: float, stop_loss: Optional[float] = None, 
                   take_profit: Optional[float] = None) -> SignalResult:
        """Record a new trading signal"""
        result = SignalResult(
            signal_id=signal_id,
            type=signal_type,
            indicator=indicator,
            entry_price=entry_price,
            entry_time=datetime.now(),
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        self.active_signals[signal_id] = result
        self.logger.info(f"New signal added: {signal_id} - {signal_type} from {indicator}")
        return result
        
    def update_signal(self, signal_id: str, current_price: float) -> Optional[SignalResult]:
        """Update an active signal with current price information"""
        if signal_id not in self.active_signals:
            return None
            
        signal = self.active_signals[signal_id]
        
        # Calculate current return
        return_pct = self._calculate_return(signal.type, signal.entry_price, current_price)
        
        # Check if signal should be completed
        if self._should_complete_signal(signal, current_price, return_pct):
            return self.complete_signal(signal_id, current_price)
            
        return signal
        
    def complete_signal(self, signal_id: str, exit_price: float) -> Optional[SignalResult]:
        """Mark a signal as complete and calculate its performance"""
        if signal_id not in self.active_signals:
            return None
            
        signal = self.active_signals[signal_id]
        signal.exit_price = exit_price
        signal.exit_time = datetime.now()
        signal.return_pct = self._calculate_return(signal.type, signal.entry_price, exit_price)
        
        # Determine outcome
        if signal.return_pct >= self.min_profit_threshold:
            signal.outcome = SignalOutcome.SUCCESS
        elif signal.return_pct <= self.max_loss_threshold:
            signal.outcome = SignalOutcome.FAILURE
            
        # Move to completed signals
        self.completed_signals.append(signal)
        del self.active_signals[signal_id]
        
        self.logger.info(f"Signal completed: {signal_id} with return {signal.return_pct:.2f}%")
        return signal
        
    def get_performance_metrics(self, timeframe: Optional[timedelta] = None) -> PerformanceMetrics:
        """Calculate performance metrics for completed signals"""
        # Filter signals by timeframe if specified
        signals = self.completed_signals
        if timeframe:
            cutoff_time = datetime.now() - timeframe
            signals = [s for s in signals if s.entry_time >= cutoff_time]
            
        if not signals:
            return PerformanceMetrics(
                total_signals=0,
                success_count=0,
                failure_count=0,
                win_rate=0.0,
                avg_return=0.0,
                avg_holding_time=timedelta(0),
                profit_factor=0.0,
                accuracy_by_indicator={},
                accuracy_by_type={}
            )
            
        # Calculate basic metrics
        success_count = sum(1 for s in signals if s.outcome == SignalOutcome.SUCCESS)
        failure_count = sum(1 for s in signals if s.outcome == SignalOutcome.FAILURE)
        total_completed = success_count + failure_count
        
        # Calculate win rate
        win_rate = success_count / total_completed if total_completed > 0 else 0.0
        
        # Calculate average return
        avg_return = sum(s.return_pct for s in signals if s.return_pct is not None) / len(signals)
        
        # Calculate average holding time
        holding_times = [s.exit_time - s.entry_time for s in signals if s.exit_time]
        avg_holding_time = sum(holding_times, timedelta(0)) / len(holding_times) if holding_times else timedelta(0)
        
        # Calculate profit factor
        winning_trades = sum(s.return_pct for s in signals if s.return_pct and s.return_pct > 0)
        losing_trades = abs(sum(s.return_pct for s in signals if s.return_pct and s.return_pct < 0))
        profit_factor = winning_trades / losing_trades if losing_trades > 0 else float('inf')
        
        # Calculate accuracy by indicator and type
        accuracy_by_indicator = self._calculate_accuracy_by_field(signals, 'indicator')
        accuracy_by_type = self._calculate_accuracy_by_field(signals, 'type')
        
        return PerformanceMetrics(
            total_signals=len(signals),
            success_count=success_count,
            failure_count=failure_count,
            win_rate=win_rate,
            avg_return=avg_return,
            avg_holding_time=avg_holding_time,
            profit_factor=profit_factor,
            accuracy_by_indicator=accuracy_by_indicator,
            accuracy_by_type=accuracy_by_type
        )
        
    def _calculate_return(self, signal_type: str, entry_price: float, current_price: float) -> float:
        """Calculate percentage return for a signal"""
        if signal_type == "BUY":
            return ((current_price - entry_price) / entry_price) * 100
        else:  # SELL
            return ((entry_price - current_price) / entry_price) * 100
            
    def _should_complete_signal(self, signal: SignalResult, current_price: float, 
                              return_pct: float) -> bool:
        """Determine if a signal should be completed based on various criteria"""
        # Check stop loss
        if signal.stop_loss and current_price <= signal.stop_loss:
            return True
            
        # Check take profit
        if signal.take_profit and current_price >= signal.take_profit:
            return True
            
        # Check timeout
        if datetime.now() - signal.entry_time >= self.signal_timeout:
            return True
            
        # Check profit/loss thresholds
        if return_pct >= self.min_profit_threshold or return_pct <= self.max_loss_threshold:
            return True
            
        return False
        
    def _calculate_accuracy_by_field(self, signals: List[SignalResult], 
                                   field: str) -> Dict[str, float]:
        """Calculate success rate grouped by a specific field"""
        results = {}
        for signal in signals:
            key = getattr(signal, field)
            if key not in results:
                results[key] = {"success": 0, "total": 0}
            if signal.outcome == SignalOutcome.SUCCESS:
                results[key]["success"] += 1
            results[key]["total"] += 1
            
        return {
            k: v["success"] / v["total"] if v["total"] > 0 else 0.0 
            for k, v in results.items()
        }

    def cleanup_expired_signals(self) -> List[SignalResult]:
        """Clean up expired signals and return them"""
        current_time = datetime.now()
        expired_signals = []
        
        for signal_id, signal in list(self.active_signals.items()):
            if current_time - signal.entry_time >= self.signal_timeout:
                signal.outcome = SignalOutcome.EXPIRED
                expired_signals.append(signal)
                self.completed_signals.append(signal)
                del self.active_signals[signal_id]
                
        return expired_signals