import pytest
from app.core.validation.price_validators import (
    PriceDataValidator,
    ValidationErrorCode
)
import pandas as pd
from datetime import datetime, timedelta

def test_validate_price_data_structure():
    validator = PriceDataValidator()
    
    # Valid data
    valid_data = {
        'symbol': 'BTC/USDT',
        'price': 50000.0,
        'volume': 1.5,
        'timestamp': datetime.now()
    }
    result = validator.validate_price_data(valid_data)
    assert result.is_valid
    
    # Missing required field
    invalid_data = {
        'symbol': 'BTC/USDT',
        'volume': 1.5,
        'timestamp': datetime.now()
    }
    result = validator.validate_price_data(invalid_data)
    assert not result.is_valid
    assert any(error.code == ValidationErrorCode.MISSING_FIELD for error in result.errors)

def test_validate_price_range():
    validator = PriceDataValidator()
    
    invalid_price_data = {
        'symbol': 'BTC/USDT',
        'price': 1e10,  # Unreasonably high price
        'volume': 1.5,
        'timestamp': datetime.now()
    }
    result = validator.validate_price_data(invalid_price_data)
    assert not result.is_valid
    assert any(error.code == ValidationErrorCode.PRICE_RANGE for error in result.errors)

def test_validate_timestamp():
    validator = PriceDataValidator()
    
    future_data = {
        'symbol': 'BTC/USDT',
        'price': 50000.0,
        'volume': 1.5,
        'timestamp': datetime.now() + timedelta(days=1)
    }
    result = validator.validate_price_data(future_data)
    assert not result.is_valid
    assert any(error.code == ValidationErrorCode.TIMESTAMP_FUTURE for error in result.errors)

def test_validate_symbol_format():
    validator = PriceDataValidator()
    
    invalid_symbol_data = {
        'symbol': 'BTCUSDT',  # Missing separator
        'price': 50000.0,
        'volume': 1.5,
        'timestamp': datetime.now()
    }
    result = validator.validate_price_data(invalid_symbol_data)
    assert not result.is_valid
    assert any(error.code == ValidationErrorCode.SYMBOL_FORMAT for error in result.errors)

def test_validate_historical_data():
    validator = PriceDataValidator()
    
    dates = pd.date_range(start='2023-01-01', end='2023-01-10', freq='1H')
    df = pd.DataFrame({
        'timestamp': dates,
        'price': 50000.0,
        'volume': 1.5,
        'symbol': 'BTC/USDT'
    })
    
    result = validator.validate_historical_data(df)
    assert result.is_valid
    
    df_with_gaps = df.copy()
    df_with_gaps = df_with_gaps.drop(df_with_gaps.index[5:10])
    result = validator.validate_historical_data(df_with_gaps)
    assert not result.is_valid
    assert any(error.code == ValidationErrorCode.TIME_CONTINUITY for error in result.errors)