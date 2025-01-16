from typing import Dict, Any, NamedTuple
from datetime import datetime, timedelta
import pandas as pd
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

class ValidationErrorCode(Enum):
    MISSING_FIELD = "missing_field"
    PRICE_RANGE = "price_range"
    VOLUME_RANGE = "volume_range"
    TIMESTAMP_FUTURE = "timestamp_future"
    SYMBOL_FORMAT = "symbol_format"
    TIME_CONTINUITY = "time_continuity"
    DUPLICATE_TIMESTAMP = "duplicate_timestamp"
    NULL_VALUES = "null_values"

@dataclass
class ValidationError:
    code: ValidationErrorCode
    message: str

@dataclass
class PriceValidationResult:
    is_valid: bool
    errors: List[ValidationError]
    warnings: List[str]
    validated_data: Optional[Dict] = None

class PriceDataValidator:
    def __init__(self):
        self.REQUIRED_FIELDS = ['symbol', 'price', 'volume', 'timestamp']
        self.MAX_PRICE = 1e10  # Maximum reasonable price
        self.MIN_PRICE = 1e-10  # Minimum reasonable price
        self.MAX_VOLUME = 1e14  # Maximum reasonable volume
        
    def validate_price_data(self, data: Dict[str, Any]) -> PriceValidationResult:
        """Validate a single price data point"""
        errors = []
        warnings = []
        
        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if field not in data:
                errors.append(ValidationError(
                    code=ValidationErrorCode.MISSING_FIELD,
                    message=f"Missing required field: {field}"
                ))
        
        if errors:
            return PriceValidationResult(False, errors, warnings)
            
        # Validate price range
        if not self.MIN_PRICE <= data['price'] <= self.MAX_PRICE:
            errors.append(ValidationError(
                code=ValidationErrorCode.PRICE_RANGE,
                message=f"Price {data['price']} outside valid range"
            ))
            
        # Validate volume
        if data['volume'] < 0 or data['volume'] > self.MAX_VOLUME:
            errors.append(ValidationError(
                code=ValidationErrorCode.VOLUME_RANGE,
                message=f"Volume {data['volume']} outside valid range"
            ))
            
        # Validate timestamp
        if data['timestamp'] > datetime.now() + timedelta(minutes=1):
            errors.append(ValidationError(
                code=ValidationErrorCode.TIMESTAMP_FUTURE,
                message="Timestamp cannot be in the future"
            ))
            
        # Validate symbol format
        if '/' not in data['symbol']:
            # Try splitting based on common quote suffixes (e.g., USDT, USDC, TUSD)
            quote_suffixes = ['USDT', 'USDC', 'TUSD', 'BTC', 'ETH']
            
            for suffix in quote_suffixes:
                if data['symbol'].endswith(suffix):
                    base = data['symbol'][:-len(suffix)]
                    quote = suffix
                    data['symbol'] = f"{base}/{quote}"
                    break
            else:
                # If no suffix matches, attempt a simple middle split for long symbols
                if len(data['symbol']) > 4:
                    base = data['symbol'][:len(data['symbol'])//2]
                    quote = data['symbol'][len(data['symbol'])//2:]
                    data['symbol'] = f"{base}/{quote}"
                elif len(data['symbol']) == 4:  # Handling very short symbols
                    base = data['symbol'][0]  # Take the first character
                    quote = data['symbol'][1:]  # The rest as quote
                    data['symbol'] = f"{base}/{quote}"
                else:
                    errors.append(ValidationError(
                        code=ValidationErrorCode.SYMBOL_FORMAT,
                        message="Invalid symbol format. Expected format: BASE/QUOTE (e.g., BTC/USDT)"
                    ))

        # Debugging: print errors if any
        if errors:
            print(f"Validation errors: {errors}")

        return PriceValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            validated_data=data if len(errors) == 0 else None
        )

        
    def validate_historical_data(self, df: pd.DataFrame) -> PriceValidationResult:
        """Validate historical price data"""
        errors = []
        warnings = []
        
        # Check required columns
        missing_cols = set(self.REQUIRED_FIELDS) - set(df.columns)
        if missing_cols:
            errors.append(ValidationError(
                code=ValidationErrorCode.MISSING_FIELD,
                message=f"Missing required columns: {missing_cols}"
            ))
            return PriceValidationResult(False, errors, warnings)
            
        # Check for null values
        null_counts = df.isnull().sum()
        if null_counts.any():
            errors.append(ValidationError(
                code=ValidationErrorCode.NULL_VALUES,
                message=f"Found null values: {null_counts[null_counts > 0].to_dict()}"
            ))
            
        # Check time continuity
        if len(df) > 1:
            time_diff = df['timestamp'].diff()
            if time_diff.max() > timedelta(hours=1):
                errors.append(ValidationError(
                    code=ValidationErrorCode.TIME_CONTINUITY,
                    message="Found gaps larger than 1 hour in time series"
                ))
                
        # Check for duplicate timestamps
        if df['timestamp'].duplicated().any():
            errors.append(ValidationError(
                code=ValidationErrorCode.DUPLICATE_TIMESTAMP,
                message="Found duplicate timestamps"
            ))
            
        # Validate each price point
        for _, row in df.iterrows():
            row_result = self.validate_price_data(row.to_dict())
            if not row_result.is_valid:
                errors.extend(row_result.errors)
                
        return PriceValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            validated_data=df if len(errors) == 0 else None
        )