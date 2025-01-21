from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from typing import List, Optional, Union
from datetime import datetime
from app.shared.database import get_db
from app.data_collectors.price_collector import CryptoPriceCollector
from app.data_processors.technical_indicators import TechnicalAnalyzer
from pydantic import BaseModel
import asyncio
import ccxt
import re
from functools import lru_cache
from datetime import datetime, timedelta
import pandas as pd
from app.services.signals.signal_generator import SignalGenerator
import aiohttp
import time

class DataCache:
    def __init__(self, max_age_seconds=30):
        self._cache = {}
        self._max_age = max_age_seconds

    def get(self, key):
        """Retrieve cached data if not expired"""
        cached = self._cache.get(key)
        if cached and (datetime.now() - cached['timestamp']).total_seconds() < self._max_age:
            return cached['data']
        return None

    def set(self, key, data):
        """Store data in cache"""
        self._cache[key] = {
            'data': data,
            'timestamp': datetime.now()
        }

# Global cache instance
data_cache = DataCache()

router = APIRouter(prefix="/api/v1")

class PriceResponse(BaseModel):
    price: float
    timestamp: datetime

class HistoricalDataPoint(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

class HistoricalDataResponse(BaseModel):
    pair: str
    timeframe: str
    data: List[HistoricalDataPoint]

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@router.get("/crypto/price/{pair}", response_model=PriceResponse)
async def get_crypto_price(pair: str):
    """Get current price for a crypto pair"""
    try:
        collector = CryptoPriceCollector()
        normalized_pair = pair.replace("-", "/").upper()
        price_data = await collector.get_current_price(normalized_pair)
        return price_data
    except ValueError:
        raise HTTPException(
            status_code=404,
            detail=f"Crypto pair {pair} not found"
        )

def normalize_symbol(symbol: str) -> str:
    """
    Normalize symbol for consistent matching
    - Remove any non-alphanumeric characters
    - Convert to uppercase
    """
    return re.sub(r'[^A-Z0-9]', '', symbol.upper())

@router.get("/crypto/pairs")
async def get_crypto_pairs(
    search: Optional[str] = Query(None),
    quote_currencies: Optional[Union[List[str], str]] = Query(default=["USDT", "BTC", "ETH", "BNB"]),
    exchange: str = Query("binance", description="Exchange to fetch pairs from")
):
    """
    Dynamically fetch all available trading pairs from a specified exchange
    
    Parameters:
    - search: Optional search term to filter pairs
    - quote_currencies: List of quote currencies to filter
    - exchange: Exchange to fetch pairs from (default: Binance)
    """
    try:
        # Ensure quote_currencies is a list
        if isinstance(quote_currencies, str):
            quote_currencies = [quote_currencies]
        
        # Normalize quote currencies
        quote_currencies = [curr.upper() for curr in quote_currencies]
        
        # Initialize the exchange
        exchange_class = getattr(ccxt, exchange.lower(), None)
        if not exchange_class:
            return {"error": f"Exchange {exchange} not supported", "pairs": []}
        
        # Create exchange instance
        ex = exchange_class({
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot'  # Focus on spot markets
            }
        })
        
        # Load markets
        await asyncio.to_thread(ex.load_markets)
        
        # Filter pairs
        all_pairs = []
        for symbol, market in ex.markets.items():
            # Check if it's a spot market and has allowed quote currency
            if (market['type'] == 'spot' and 
                market['quote'] in quote_currencies and 
                market['active']):
                pair_info = {
                    'symbol': symbol,
                    'base': market['base'],
                    'quote': market['quote'],
                    'category': market.get('category', 'Spot'),
                    'keywords': [market['base'].lower(), market['quote'].lower()]
                }
                all_pairs.append(pair_info)
        
        # Search filtering if search term is provided
        if search:
            # Normalize search term
            search_norm = normalize_symbol(search)
            
            # Filter pairs
            all_pairs = [
                pair for pair in all_pairs
                if (search_norm in normalize_symbol(pair['symbol']) or
                    search_norm in normalize_symbol(pair['base']) or
                    search_norm in normalize_symbol(pair['quote']) or
                    any(search_norm in normalize_symbol(keyword) for keyword in pair.get('keywords', [])))
            ]
        
        # Sort pairs by symbol
        all_pairs.sort(key=lambda x: x['symbol'])
        
        return {
            "total_pairs": len(all_pairs),
            "pairs": all_pairs
        }
    
    except Exception as e:
        return {
            "error": f"Error fetching pairs: {str(e)}",
            "pairs": []
        }
    
@router.websocket("/crypto/ws/{pair}")
async def websocket_endpoint(websocket: WebSocket, pair: str):
    await websocket.accept()
    
    try:
        collector = CryptoPriceCollector()
        normalized_pair = pair.replace("-", "/").upper()
        
        last_price = None
        last_update_time = datetime.now()
        
        while True:
            current_time = datetime.now()

            # Get current price
            current_price = await collector.get_current_price(normalized_pair)

            # Only fetch new data every 10 seconds
            if (current_time - last_update_time).total_seconds() >= 10:
                current_price = await collector.get_current_price(normalized_pair)
            
                # Calculate price change
                if last_price:
                    price_change = ((current_price['price'] - last_price) / last_price) * 100
                else:
                    price_change = 0
            
                # Create response with properly formatted timestamp
                response_data = {
                    "price": current_price['price'],
                    "timestamp": current_price['timestamp'].isoformat(),  # Convert datetime to ISO string
                    "priceChange24h": price_change
                }
                
                await websocket.send_json(response_data)
            
                last_price = current_price['price']
                last_update_time = current_time
            
            # Reduce CPU usage
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        print(f"Client disconnected from {pair} WebSocket")
        
    except Exception as e:
        print(f"Error occurred: {e}")
        
    finally:
        await websocket.close()

@router.get("/crypto/historical/{pair}", response_model=HistoricalDataResponse)
async def get_historical_data(
    pair: str,
    timeframe: str,
):
    """Get historical price data with caching"""
    cache_key = f"{pair}_{timeframe}"
    
    # Try to get cached data
    cached_data = data_cache.get(cache_key)
    if cached_data:
        return cached_data

    """Get historical price data"""
    try:
        collector = CryptoPriceCollector()
        normalized_pair = pair.replace("-", "/").upper()
        data = collector.fetch_historical_data(
            normalized_pair,
            timeframe=timeframe
        )

        data = data.to_dict(orient='records')
        
        # Ensure that the data is formatted as a list of dictionaries matching HistoricalDataPoint schema
        formatted_data = [
            HistoricalDataPoint(
                timestamp=entry['timestamp'],
                open=entry['open'],
                high=entry['high'],
                low=entry['low'],
                close=entry['close'],
                volume=entry['volume']
            ) for entry in data
        ]

        result = {
            "pair": normalized_pair,
            "timeframe": timeframe,
            "data": formatted_data
        }

        # Cache the result
        data_cache.set(cache_key, result)

        return result
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    
@router.get("/crypto/indicators/{pair}")
async def get_indicators(
    pair: str,
    indicators: str = Query(..., description="Comma-separated list of indicators"),
    timeframe: str = Query("1h", regex="^(1h|4h|1d)$")
):
    """Get technical indicators and signals for a crypto pair with caching"""
    try:
        cache_key = f"{pair}_{indicators}_{timeframe}"
        cached_result = data_cache.get(cache_key)
        if cached_result:
            return cached_result

        print(f"Calculating indicators for {pair}, timeframe: {timeframe}")
        
        collector = CryptoPriceCollector()
        normalized_pair = pair.replace("-", "/").upper()
        
        # Use the same timeframe as requested - these are standard exchange timeframes
        print(f"Fetching historical data with timeframe: {timeframe}")
        
        data = collector.fetch_historical_data(
            symbol=normalized_pair,
            timeframe=timeframe  # Use the requested timeframe directly
        )
        
        if data is None or len(data) == 0:
            raise ValueError(f"No historical data available for {normalized_pair}")
            
        print(f"Data fetched, length: {len(data)}")
        analyzer = TechnicalAnalyzer(data)
        
        # Calculate requested indicators
        result = {}
        indicator_list = [i.strip().lower() for i in indicators.split(",")]
        
        # Calculate RSI
        rsi_values = analyzer.calculate_rsi()
        if "rsi" in indicator_list:
            result["rsi"] = float(rsi_values.iloc[-1])
        
        # Calculate MACD
        macd_line, signal, hist = analyzer.calculate_macd()
        if "macd" in indicator_list:
            result["macd"] = {
                "macd": float(macd_line.iloc[-1]),
                "signal": float(signal.iloc[-1]),
                "histogram": float(hist.iloc[-1])
            }
        
        # Calculate Bollinger Bands
        upper, middle, lower = analyzer.calculate_bollinger_bands()
        if "bb" in indicator_list:
            result["bb"] = {
                "upper": float(upper.iloc[-1]),
                "middle": float(middle.iloc[-1]),
                "lower": float(lower.iloc[-1])
            }

        # Prepare data for signal generation
        latest_indicators = pd.DataFrame({
            'timestamp': [data.index[-1] if data.index is not None else data['timestamp'].iloc[-1]],
            'close': [data['close'].iloc[-1]],
            'rsi': [rsi_values.iloc[-1]],
            'macd': [macd_line.iloc[-1]],
            'macd_signal': [signal.iloc[-1]],
            'bb_upper': [upper.iloc[-1]],
            'bb_lower': [lower.iloc[-1]]
        })

        # Generate signals
        signal_generator = SignalGenerator()
        signals = signal_generator.generate_signals(latest_indicators)
        
        result["signals"] = [
            {
                "type": signal.type.value,
                "indicator": signal.indicator,
                "strength": float(signal.strength),
                "message": signal.message
            }
            for signal in signals
        ]
            
        data_cache.set(cache_key, result)
        return result
        
    except ValueError as e:
        print(f"ValueError in indicator calculation: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        print(f"Unexpected error in indicator calculation: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while calculating indicators: {str(e)}"
        )

@lru_cache(maxsize=1)
def get_cached_market_data():
    return {
        'data': [],
        'timestamp': 0
    }

@router.get("/crypto/market")
async def get_market_overview(
    quote_currency: str = Query("USDT", description="Quote currency for market data"),
    limit: int = Query(50, ge=1, le=250, description="Number of top cryptocurrencies to fetch"),
    sort_by: str = Query("market_cap", description="Sort field (market_cap, price, volume)")
):
    """
    Fetch top cryptocurrencies with market data
    
    Parameters:
    - quote_currency: Currency to use for pricing (default USDT)
    - limit: Number of top cryptocurrencies to return
    - sort_by: Field to sort the results
    """
    try:
        # Check cache first
        cached_data = get_cached_market_data()
        current_time = time.time()
        
        # Return cached data if it's less than 5 minutes old
        if cached_data['data'] and (current_time - cached_data['timestamp']) < 300:
            return cached_data['data']
        
        # Initialize exchange
        exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot'
            }
        })
        
        # Fetch top markets by volume
        markets = await asyncio.to_thread(exchange.fetch_tickers)
        
        # Filter and process markets
        market_data = []
        for symbol, ticker in markets.items():
            # Check market conditions
            market = exchange.markets.get(symbol, {})
            if (market.get('type') == 'spot' and 
                market.get('quote') == quote_currency and 
                market.get('active', False)):
                
                try:
                    # Prepare market entry
                    market_entry = {
                        'symbol': symbol,
                        'price': ticker['last'] or 0,
                        'change_24h': ticker['percentage'] or 0,
                        'volume_24h': ticker['quoteVolume'] or 0,
                        'market_cap': (ticker['last'] or 0) * (ticker['quoteVolume'] or 0),  # Rough market cap estimate
                        'last_updated': ticker['timestamp']
                    }
                    
                    market_data.append(market_entry)
                except Exception as e:
                    print(f"Error processing {symbol}: {str(e)}")
        
        # Sort the market data
        valid_sort_fields = ['price', 'change_24h', 'volume_24h', 'market_cap']
        if sort_by not in valid_sort_fields:
            sort_by = 'market_cap'
        
        # Sort and limit results
        sorted_market_data = sorted(
            market_data, 
            key=lambda x: x.get(sort_by, 0), 
            reverse=True
        )[:limit]
        
        # Cache the result
        cache_data = get_cached_market_data()
        cache_data['data'] = sorted_market_data
        cache_data['timestamp'] = current_time
        
        return sorted_market_data
    
    except Exception as e:
        print(f"Critical error in market overview: {str(e)}")
        import traceback
        traceback.print_exc()
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch market data: {str(e)}"
        )