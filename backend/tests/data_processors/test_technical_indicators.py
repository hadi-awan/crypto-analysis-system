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

def test_calculate_stochastic(sample_data):
    analyzer = TechnicalAnalyzer(sample_data)
    k, d = analyzer.calculate_stochastic(period=14, smooth_k=3, smooth_d=3)

    # Assert the lengths match
    assert len(k) == len(sample_data)
    assert len(d) == len(sample_data)

    # Calculate the number of NaN values due to initialization
    nan_count = 14 + 3 - 1  # Stochastic period + smoothing

    # Check that values are not null after the initialization period
    assert not k[nan_count:].isnull().any()
    assert not d[nan_count:].isnull().any()


def test_calculate_ichimoku(sample_data):
    analyzer = TechnicalAnalyzer(sample_data)
    tenkan, kijun, senkou_a, senkou_b, chikou = analyzer.calculate_ichimoku()

    # Assert the lengths match
    assert len(tenkan) == len(sample_data)
    assert len(kijun) == len(sample_data)
    assert len(senkou_a) == len(sample_data)
    assert len(senkou_b) == len(sample_data)
    assert len(chikou) == len(sample_data)

    # Calculate the initialization periods
    senkou_b_nan_count = 52  # Lookback for Senkou B
    senkou_a_nan_count = 26 + 52  # Lookback for Senkou B + 26-period shift

    # Validate after the necessary periods
    assert not tenkan[9:].isnull().any()  # 9-period Tenkan
    assert not kijun[26:].isnull().any()  # 26-period Kijun
    assert not senkou_a[senkou_a_nan_count:].isnull().any()
    assert not senkou_b[senkou_b_nan_count:].isnull().any()
    assert not chikou.isnull().any()  # Chikou is shifted backward

def test_calculate_fibonacci_retracements(sample_data):
    analyzer = TechnicalAnalyzer(sample_data)
    retracements = analyzer.calculate_fibonacci_retracements(period=20)

    # Ensure all levels are calculated
    assert len(retracements) == 6

    # Validate retracement levels
    assert retracements['0.0%'] == sample_data['close'].iloc[-1]
    assert retracements['100.0%'] == sample_data['close'].iloc[-20]

def test_calculate_obv(sample_data):
    analyzer = TechnicalAnalyzer(sample_data)
    obv = analyzer.calculate_obv()
    
    assert len(obv) == len(sample_data)
    assert not obv.isnull().any()
    assert isinstance(obv, pd.Series)