# tests/services/filters/test_signal_filter.py
import pytest
from datetime import datetime, timedelta
from app.services.signals.signal_filter import SignalFilter, FilterConfig
from app.services.signals.signal_generator import Signal, SignalType

@pytest.fixture
def base_signal():
    return Signal(
        type=SignalType.BUY,
        indicator="RSI",
        strength=0.8,
        message="Test signal",
        timestamp=datetime.now()
    )

def test_strength_filter():
    config = FilterConfig(min_strength=0.7)
    signal_filter = SignalFilter(config)
    
    strong_signal = Signal(
        type=SignalType.BUY,
        indicator="RSI",
        strength=0.8,
        message="Strong signal",
        timestamp=datetime.now()
    )
    
    weak_signal = Signal(
        type=SignalType.BUY,
        indicator="RSI",
        strength=0.3,
        message="Weak signal",
        timestamp=datetime.now()
    )
    
    assert signal_filter.filter_signal(strong_signal) == True
    assert signal_filter.filter_signal(weak_signal) == False

def test_cooldown_filter(base_signal):
    config = FilterConfig(cooldown_period=300)  # 5 minutes cooldown
    signal_filter = SignalFilter(config)
    
    # First signal should pass
    assert signal_filter.filter_signal(base_signal) == True
    
    # Same type of signal within cooldown should be blocked
    similar_signal = Signal(
        type=base_signal.type,
        indicator=base_signal.indicator,
        strength=base_signal.strength,
        message="Similar signal",
        timestamp=datetime.now()
    )
    assert signal_filter.filter_signal(similar_signal) == False

def test_indicator_allowlist():
    config = FilterConfig(allowed_indicators=["RSI", "MACD"])
    signal_filter = SignalFilter(config)
    
    rsi_signal = Signal(
        type=SignalType.BUY,
        indicator="RSI",
        strength=0.8,
        message="RSI signal",
        timestamp=datetime.now()
    )
    
    bb_signal = Signal(
        type=SignalType.BUY,
        indicator="BB",
        strength=0.8,
        message="BB signal",
        timestamp=datetime.now()
    )
    
    assert signal_filter.filter_signal(rsi_signal) == True
    assert signal_filter.filter_signal(bb_signal) == False

def test_confirmation_requirement():
    config = FilterConfig(required_confirmations=2)
    signal_filter = SignalFilter(config)
    now = datetime.now()
    
    # First signal
    signal1 = Signal(
        type=SignalType.BUY,
        indicator="RSI",
        strength=0.8,
        message="RSI Buy",
        timestamp=now
    )
    
    # Should not pass without confirmation
    assert signal_filter.filter_signal(signal1) == False
    signal_filter.update_recent_signals(signal1)
    
    # Second signal from different indicator
    signal2 = Signal(
        type=SignalType.BUY,
        indicator="MACD",
        strength=0.8,
        message="MACD Buy",
        timestamp=now + timedelta(seconds=1)
    )
    
    # Should pass with confirmation
    signal_filter.update_recent_signals(signal2)
    assert signal_filter.filter_signal(signal2) == True