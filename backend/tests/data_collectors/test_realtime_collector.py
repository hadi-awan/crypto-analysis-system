import pytest
from datetime import datetime, timedelta
import pandas as pd
from app.data_collectors.price_collector import CryptoPriceCollector

def test_price_collector_initialization():
    collector = CryptoPriceCollector()
    assert collector is not None
    assert hasattr(collector, 'exchange')

def test_fetch_historical_data():
    collector = CryptoPriceCollector()
    symbol = "BTC/USDT"
    timeframe = "1h"
    
    # Fetch last 24 hours of data
    end_time = datetime.now()
    start_time = end_time - timedelta(days=1)
    
    df = collector.fetch_historical_data(
        symbol=symbol,
        timeframe=timeframe,
        start_time=start_time,
        end_time=end_time
    )
    
    # Check if we got a DataFrame
    assert isinstance(df, pd.DataFrame)
    
    # Check if we have the expected columns
    expected_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    assert all(col in df.columns for col in expected_columns)
    
    # Check data types
    assert pd.api.types.is_numeric_dtype(df['close'])
    assert pd.api.types.is_numeric_dtype(df['volume'])
    
    # Check that we have some data
    assert len(df) > 0

def test_fetch_historical_data_with_invalid_symbol():
    collector = CryptoPriceCollector()
    with pytest.raises(ValueError):
        collector.fetch_historical_data(
            symbol="INVALID/PAIR",
            timeframe="1h"
        )

def test_supported_timeframes():
    collector = CryptoPriceCollector()
    timeframes = collector.get_supported_timeframes()
    assert isinstance(timeframes, list)
    assert "1m" in timeframes
    assert "1h" in timeframes
    assert "1d" in timeframes