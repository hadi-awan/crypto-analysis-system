# tests/services/signals/test_signal_generator.py
import pytest
import pandas as pd
from datetime import datetime
from app.services.signals.signal_generator import SignalGenerator, Signal, SignalType

def create_test_data(**kwargs):
    """Helper function to create test data with defaults"""
    defaults = {
        'timestamp': datetime.now(),
        'close': 50000.0,
        'volume': 1000.0,
    }
    return pd.DataFrame([{**defaults, **kwargs}])

def test_signal_generator_initialization():
    generator = SignalGenerator()
    assert hasattr(generator, 'strategies')
    assert len(generator.strategies) > 0

def test_rsi_overbought_signal():
    generator = SignalGenerator()
    data = create_test_data(rsi=75)  # Only need RSI data
    
    signals = generator.generate_signals(data)
    assert len(signals) > 0
    rsi_signals = [s for s in signals if s.indicator == 'RSI']
    assert len(rsi_signals) == 1
    assert rsi_signals[0].type == SignalType.SELL

def test_rsi_oversold_signal():
    generator = SignalGenerator()
    data = create_test_data()
    data['rsi'] = 25  # Oversold condition
    
    signals = generator.generate_signals(data)
    assert len(signals) > 0
    assert any(s.type == SignalType.BUY for s in signals)
    assert any(s.indicator == 'RSI' for s in signals)

def test_macd_crossover_signal():
    generator = SignalGenerator()
    data = create_test_data(
        macd=60,
        macd_signal=50
    )
    
    signals = generator.generate_signals(data)
    assert len(signals) > 0
    macd_signals = [s for s in signals if s.indicator == 'MACD']
    assert len(macd_signals) == 1
    assert macd_signals[0].type == SignalType.BUY

def test_bollinger_bands_signal():
    generator = SignalGenerator()
    data = create_test_data(
        close=47500,
        bb_upper=52000,
        bb_lower=48000
    )
    
    signals = generator.generate_signals(data)
    assert len(signals) > 0
    bb_signals = [s for s in signals if s.indicator == 'BB']
    assert len(bb_signals) == 1
    assert bb_signals[0].type == SignalType.BUY

def test_multiple_signals():
    generator = SignalGenerator()
    data = create_test_data()
    # Create conditions for multiple signals
    data['rsi'] = 75  # Overbought
    data['macd'] = 60
    data['macd_signal'] = 50  # MACD crossover
    
    signals = generator.generate_signals(data)
    assert len(signals) > 1  # Should get multiple signals

def test_signal_strength():
    generator = SignalGenerator()
    data = create_test_data(
        rsi=85,  # Very overbought
        close=50000,
        timestamp=datetime.now()
    )
    
    signals = generator.generate_signals(data)
    assert len(signals) > 0, "Should generate at least one signal"
    rsi_signals = [s for s in signals if s.indicator == 'RSI']
    assert len(rsi_signals) > 0, "Should generate RSI signal"
    assert rsi_signals[0].strength > 0.8, "Should have strong signal strength"

def test_stochastic_signals():
    generator = SignalGenerator()
    
    # Test oversold
    oversold_data = create_test_data(
        stoch_k=15,
        stoch_d=18
    )
    signals = generator.generate_signals(oversold_data)
    stoch_signals = [s for s in signals if s.indicator == 'STOCH']
    assert len(stoch_signals) == 1
    assert stoch_signals[0].type == SignalType.BUY
    
    # Test overbought
    overbought_data = create_test_data(
        stoch_k=85,
        stoch_d=82
    )
    signals = generator.generate_signals(overbought_data)
    stoch_signals = [s for s in signals if s.indicator == 'STOCH']
    assert len(stoch_signals) == 1
    assert stoch_signals[0].type == SignalType.SELL

def test_multiple_signals():
    generator = SignalGenerator()
    data = create_test_data(
        rsi=75,
        macd=60,
        macd_signal=50,
        stoch_k=85,
        stoch_d=82,
        close=52000,
        bb_upper=51000,
        bb_lower=49000
    )
    
    signals = generator.generate_signals(data)
    assert len(signals) > 1  # Should get multiple signals