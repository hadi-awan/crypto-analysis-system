import ccxt
import pandas as pd
from datetime import datetime
from typing import List, Optional

class CryptoPriceCollector:
    """
    A class to collect cryptocurrency price data from exchanges
    """
    
    def __init__(self, exchange_id: str = 'binance'):
        """
        Initialize the price collector with specified exchange
        
        Args:
            exchange_id (str): The exchange ID to use (default: 'binance')
        """
        self.exchange = getattr(ccxt, exchange_id)()
        self.supported_timeframes = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d']
    
    def get_supported_timeframes(self) -> List[str]:
        """Get list of supported timeframes"""
        return self.supported_timeframes
    
    def fetch_historical_data(
        self,
        symbol: str,
        timeframe: str = '1h',
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Fetch historical OHLCV data for a given symbol and timeframe
        
        Args:
            symbol (str): Trading pair symbol (e.g., 'BTC/USDT')
            timeframe (str): Timeframe for the data (default: '1h')
            start_time (datetime, optional): Start time for data collection
            end_time (datetime, optional): End time for data collection
            
        Returns:
            pd.DataFrame: DataFrame containing the historical data
        """
        if timeframe not in self.supported_timeframes:
            raise ValueError(f"Unsupported timeframe. Must be one of {self.supported_timeframes}")
            
        try:
            # Convert times to timestamps if provided
            since = int(start_time.timestamp() * 1000) if start_time else None
            until = int(end_time.timestamp() * 1000) if end_time else None
            
            # Fetch the OHLCV data
            ohlcv = self.exchange.fetch_ohlcv(
                symbol,
                timeframe=timeframe,
                since=since,
                limit=1000  # Most exchanges limit to 1000 candles per request
            )
            
            # Convert to DataFrame
            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            return df
            
        except ccxt.ExchangeError as e:
            if "symbol" in str(e).lower():
                raise ValueError(f"Invalid symbol: {symbol}")
            raise e