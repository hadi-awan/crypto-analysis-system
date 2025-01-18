# tests/services/performance/test_performance_tracker.py
import pytest
from datetime import datetime, timedelta
from app.services.performance.performance_tracker import (
    PerformanceTracker, 
    SignalOutcome,
    SignalResult
)

@pytest.fixture
def tracker():
    return PerformanceTracker()

@pytest.fixture
def sample_signal_data():
    return {
        "signal_id": "test_signal_1",
        "signal_type": "BUY",
        "indicator": "RSI",
        "entry_price": 100.0
    }

def test_add_signal(tracker, sample_signal_data):
    """Test adding a new signal"""
    result = tracker.add_signal(**sample_signal_data)
    
    assert result.signal_id == sample_signal_data["signal_id"]
    assert result.type == sample_signal_data["signal_type"]
    assert result.indicator == sample_signal_data["indicator"]
    assert result.entry_price == sample_signal_data["entry_price"]
    assert result.outcome == SignalOutcome.PENDING
    assert result.signal_id in tracker.active_signals

def test_update_signal_profit(tracker, sample_signal_data):
    """Test updating signal with profitable price movement"""
    tracker.add_signal(**sample_signal_data)
    current_price = 105.0  # 5% profit
    
    result = tracker.update_signal(sample_signal_data["signal_id"], current_price)
    
    assert result is not None
    assert result.signal_id == sample_signal_data["signal_id"]
    # Signal should complete due to reaching profit threshold
    assert result.signal_id not in tracker.active_signals
    assert len(tracker.completed_signals) == 1
    assert tracker.completed_signals[0].outcome == SignalOutcome.SUCCESS

def test_update_signal_loss(tracker, sample_signal_data):
    """Test updating signal with losing price movement"""
    tracker.add_signal(**sample_signal_data)
    current_price = 98.0  # 2% loss
    
    result = tracker.update_signal(sample_signal_data["signal_id"], current_price)
    
    assert result is not None
    assert result.signal_id == sample_signal_data["signal_id"]
    # Signal should complete due to reaching loss threshold
    assert result.signal_id not in tracker.active_signals
    assert len(tracker.completed_signals) == 1
    assert tracker.completed_signals[0].outcome == SignalOutcome.FAILURE

def test_stop_loss_trigger(tracker):
    """Test signal completion due to stop loss"""
    signal = tracker.add_signal(
        signal_id="stop_loss_test",
        signal_type="BUY",
        indicator="RSI",
        entry_price=100.0,
        stop_loss=95.0
    )
    
    # Update with price at stop loss
    result = tracker.update_signal("stop_loss_test", 95.0)
    
    assert result is not None
    assert result.signal_id not in tracker.active_signals
    assert len(tracker.completed_signals) == 1
    assert tracker.completed_signals[0].outcome == SignalOutcome.FAILURE

def test_take_profit_trigger(tracker):
    """Test signal completion due to take profit"""
    signal = tracker.add_signal(
        signal_id="take_profit_test",
        signal_type="BUY",
        indicator="RSI",
        entry_price=100.0,
        take_profit=110.0
    )
    
    # Update with price at take profit
    result = tracker.update_signal("take_profit_test", 110.0)
    
    assert result is not None
    assert result.signal_id not in tracker.active_signals
    assert len(tracker.completed_signals) == 1
    assert tracker.completed_signals[0].outcome == SignalOutcome.SUCCESS

def test_signal_expiry(tracker, sample_signal_data):
    """Test signal expiration handling"""
    signal = tracker.add_signal(**sample_signal_data)
    
    # Manually set entry time to past timeout threshold
    signal.entry_time = datetime.now() - tracker.signal_timeout - timedelta(minutes=1)
    
    expired_signals = tracker.cleanup_expired_signals()
    
    assert len(expired_signals) == 1
    assert expired_signals[0].outcome == SignalOutcome.EXPIRED
    assert sample_signal_data["signal_id"] not in tracker.active_signals
    assert len(tracker.completed_signals) == 1

def test_performance_metrics_calculation(tracker):
    """Test calculation of performance metrics"""
    # Add a mix of successful and failed signals
    signals = [
        {"signal_id": "success_1", "signal_type": "BUY", "indicator": "RSI", "entry_price": 100.0},
        {"signal_id": "success_2", "signal_type": "SELL", "indicator": "MACD", "entry_price": 100.0},
        {"signal_id": "failure_1", "signal_type": "BUY", "indicator": "RSI", "entry_price": 100.0}
    ]
    
    for signal_data in signals:
        tracker.add_signal(**signal_data)
    
    # Complete signals with different outcomes
    tracker.complete_signal("success_1", 105.0)  # 5% profit
    tracker.complete_signal("success_2", 95.0)   # 5% profit (for SELL)
    tracker.complete_signal("failure_1", 98.0)   # 2% loss
    
    metrics = tracker.get_performance_metrics()
    
    assert metrics.total_signals == 3
    assert metrics.success_count == 2
    assert metrics.failure_count == 1
    assert metrics.win_rate == pytest.approx(0.6667, rel=0.01)
    assert "RSI" in metrics.accuracy_by_indicator
    assert "MACD" in metrics.accuracy_by_indicator
    assert "BUY" in metrics.accuracy_by_type
    assert "SELL" in metrics.accuracy_by_type

def test_sell_signal_performance(tracker):
    """Test performance calculation for SELL signals"""
    signal = tracker.add_signal(
        signal_id="sell_test",
        signal_type="SELL",
        indicator="RSI",
        entry_price=100.0
    )
    
    # For SELL signals, price going down means profit
    result = tracker.update_signal("sell_test", 95.0)  # 5% profit for SELL
    
    assert result is not None
    assert result.signal_id not in tracker.active_signals
    assert len(tracker.completed_signals) == 1
    assert tracker.completed_signals[0].outcome == SignalOutcome.SUCCESS
    assert tracker.completed_signals[0].return_pct == pytest.approx(5.0)

def test_invalid_signal_handling(tracker):
    """Test handling of invalid signal operations"""
    # Update non-existent signal
    result = tracker.update_signal("non_existent", 100.0)
    assert result is None
    
    # Complete non-existent signal
    result = tracker.complete_signal("non_existent", 100.0)
    assert result is None

def test_performance_metrics_timeframe(tracker):
    """Test performance metrics with timeframe filtering"""
    # Add old signal
    old_signal = tracker.add_signal(
        signal_id="old_signal",
        signal_type="BUY",
        indicator="RSI",
        entry_price=100.0
    )
    old_signal.entry_time = datetime.now() - timedelta(days=2)
    tracker.complete_signal("old_signal", 105.0)
    
    # Add recent signal
    tracker.add_signal(
        signal_id="recent_signal",
        signal_type="BUY",
        indicator="RSI",
        entry_price=100.0
    )
    tracker.complete_signal("recent_signal", 105.0)
    
    # Get metrics for last day
    metrics = tracker.get_performance_metrics(timeframe=timedelta(days=1))
    
    assert metrics.total_signals == 1  # Only recent signal should be counted
    assert metrics.success_count == 1