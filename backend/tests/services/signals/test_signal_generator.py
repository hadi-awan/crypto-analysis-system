# tests/services/signals/test_signal_generator.py
import pytest
import pandas as pd
from datetime import datetime
from app.services.signals.signal_generator import SignalGenerator, Signal, SignalType

def create_test_data():
    return pd.DataFrame({
        'timestamp': [datetime.now()],
        'close': [50000],
        'rsi': [70],
        'macd': [100],
        'macd_signal': [50],
        'upper_band': [52000],
        'middle_band': [50000],
        'lower_band': [48000]
    })

def test_signal_generator_initialization():
    generator = SignalGenerator()
    assert hasattr(generator, 'strategies')
    assert len(generator.strategies) > 0

def test_rsi_overbought_signal():
    generator = SignalGenerator()
    data = create_test_data()
    data['rsi'] = 75  # Overbought condition
    
    signals = generator.generate_signals(data)
    assert len(signals) > 0
    assert any(s.type == SignalType.SELL for s in signals)
    assert any(s.indicator == 'RSI' for s in signals)

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
    data = create_test_data()
    data['macd'] = 60
    data['macd_signal'] = 50  # MACD crosses above signal line
    
    signals = generator.generate_signals(data)
    assert len(signals) > 0
    assert any(s.type == SignalType.BUY for s in signals)
    assert any(s.indicator == 'MACD' for s in signals)

def test_bollinger_bands_signal():
    generator = SignalGenerator()
    data = create_test_data()
    data['close'] = 47500  # Price below lower band
    data['lower_band'] = 48000
    
    signals = generator.generate_signals(data)
    assert len(signals) > 0
    assert any(s.type == SignalType.BUY for s in signals)
    assert any(s.indicator == 'BB' for s in signals)

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
    data = create_test_data()
    data['rsi'] = 85  # Very overbought
    
    signals = generator.generate_signals(data)
    assert any(s.strength > 0.8 for s in signals)  # Strong signal