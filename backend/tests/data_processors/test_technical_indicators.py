import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from app.data_processors.technical_indicators import TechnicalAnalyzer

@pytest.fixture
def sample_data():
    # Create sample price data for testing
    dates = pd.date_range(start='2023-01-01', end='2023-01-30', freq='1H')
    np.random.seed(42)  # For reproducibility
    
    df = pd.DataFrame({
        'timestamp': dates,
        'close': np.random.normal(50000, 1000, len(dates)),
        'high': np.random.normal(51000, 1000, len(dates)),
        'low': np.random.normal(49000, 1000, len(dates)),
        'volume': np.random.normal(100, 10, len(dates))
    })
    
    # Ensure high > close > low
    df['high'] = df[['high', 'close']].max(axis=1)
    df['low'] = df[['low', 'close']].min(axis=1)
    return df

def test_calculate_sma(sample_data):
    analyzer = TechnicalAnalyzer(sample_data)
    sma = analyzer.calculate_sma(period=20)
    
    assert len(sma) == len(sample_data)
    assert not sma.isnull().all()
    assert isinstance(sma, pd.Series)
    
    # First n-1 values should be NaN for n-period SMA
    assert sma[:19].isnull().all()
    assert not sma[19:].isnull().any()

def test_calculate_ema(sample_data):
    analyzer = TechnicalAnalyzer(sample_data)
    ema = analyzer.calculate_ema(period=20)
    
    assert len(ema) == len(sample_data)
    assert isinstance(ema, pd.Series)
    assert not ema[19:].isnull().any()

def test_calculate_rsi(sample_data):
    analyzer = TechnicalAnalyzer(sample_data)
    rsi = analyzer.calculate_rsi(period=14)
    
    assert len(rsi) == len(sample_data)
    assert isinstance(rsi, pd.Series)
    assert not rsi[14:].isnull().any()
    assert (rsi >= 0).all() and (rsi <= 100).all()

def test_calculate_macd(sample_data):
    analyzer = TechnicalAnalyzer(sample_data)
    macd, signal, hist = analyzer.calculate_macd()
    
    assert len(macd) == len(sample_data)
    assert len(signal) == len(sample_data)
    assert len(hist) == len(sample_data)
    assert not macd[33:].isnull().any()  # 26 + 12 - 1 periods needed

def test_calculate_bollinger_bands(sample_data):
    analyzer = TechnicalAnalyzer(sample_data)
    upper, middle, lower = analyzer.calculate_bollinger_bands(period=20)
    
    # Check lengths
    assert len(upper) == len(sample_data)
    assert len(middle) == len(sample_data)
    assert len(lower) == len(sample_data)
    
    # Drop NaN values for comparison
    valid_idx = ~(upper.isna() | middle.isna() | lower.isna())
    
    # Check band relationships
    assert (upper[valid_idx] >= middle[valid_idx]).all(), "Upper band should be >= middle band"
    assert (middle[valid_idx] >= lower[valid_idx]).all(), "Middle band should be >= lower band"
    
    # Check spacing
    band_spacing = (upper - middle).mean()
    assert band_spacing > 0, "Average band spacing should be positive"

def test_calculate_atr(sample_data):
    analyzer = TechnicalAnalyzer(sample_data)
    atr = analyzer.calculate_atr(period=14)
    
    assert len(atr) == len(sample_data)
    assert not atr[14:].isnull().any()
    assert (atr >= 0).all()

def test_calculate_volatility(sample_data):
    analyzer = TechnicalAnalyzer(sample_data)
    volatility = analyzer.calculate_volatility(period=20)
    
    assert len(volatility) == len(sample_data)
    assert not volatility[20:].isnull().any()
    assert (volatility >= 0).all()