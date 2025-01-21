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
import numpy as np

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

@router.get("/crypto/comprehensive-analysis/{pair}")
async def get_comprehensive_analysis(
    pair: str,
    timeframe: str = Query("1d", description="Timeframe for analysis"),
    quote_currency: str = Query("USDT", description="Quote currency")
):
    """
    Fetch comprehensive cryptocurrency analysis
    
    Parameters:
    - pair: Trading pair
    - timeframe: Analysis timeframe
    - quote_currency: Quote currency for pricing
    """
    try:
        # Normalize pair
        normalized_pair = pair.replace('-', '/').upper()
        
        # Initialize services
        collector = CryptoPriceCollector()
        
        # Fetch historical data
        historical_data = await asyncio.to_thread(
            collector.fetch_historical_data, 
            normalized_pair, 
            timeframe=timeframe
        )
        
        # Initialize analyzer with historical data
        analyzer = TechnicalAnalyzer(historical_data)
        
        # Historical Performance Analysis
        yearly_returns = _calculate_yearly_returns(historical_data)
        total_return = _calculate_total_return(historical_data)
        volatility = _calculate_volatility(historical_data)
        max_drawdown = _calculate_max_drawdown(historical_data)
        
        # Volume Analysis
        volume_analysis = _analyze_volume(historical_data)
        
        # Correlation Analysis
        correlations = _calculate_correlations(normalized_pair)
        
        # Support and Resistance Levels
        support_resistance = _identify_support_resistance_levels(historical_data)
        
        # Compile comprehensive analysis
        comprehensive_analysis = {
            "historical_performance": {
                "yearly_returns": yearly_returns,
                "total_return": total_return,
                "volatility": volatility,
                "max_drawdown": max_drawdown
            },
            "volume_analysis": volume_analysis,
            "correlations": correlations,
            "support_resistance": support_resistance
        }
        
        return comprehensive_analysis
    
    except Exception as e:
        print(f"Error in comprehensive analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch comprehensive analysis: {str(e)}"
        )

def _calculate_yearly_returns(data):
    """
    Calculate yearly returns from historical price data with more comprehensive calculation
    """
    if len(data) == 0:
        return []
    
    # Convert to datetime index if not already
    if not isinstance(data.index, pd.DatetimeIndex):
        data.index = pd.to_datetime(data.index)
    
    # Group by year and calculate returns
    yearly_returns = []
    
    # Get unique years in the data
    years = data.index.year.unique()
    
    for year in years:
        # Filter data for the specific year
        yearly_data = data[data.index.year == year]
        
        if len(yearly_data) > 0:
            # First and last price of the year
            first_price = yearly_data.iloc[0]['close']
            last_price = yearly_data.iloc[-1]['close']
            
            # Calculate yearly return
            yearly_return = ((last_price - first_price) / first_price) * 100
            
            yearly_returns.append({
                "year": year,
                "return_percentage": float(yearly_return)
            })
    
    return yearly_returns

def _calculate_total_return(data):
    """Calculate total return percentage"""
    if len(data) > 0:
        first_price = data.iloc[0]['close']
        last_price = data.iloc[-1]['close']
        return ((last_price - first_price) / first_price) * 100
    return 0

def _calculate_volatility(data):
    """Calculate price volatility"""
    returns = np.log(data['close'] / data['close'].shift(1))
    return float(returns.std() * np.sqrt(len(returns)) * 100)

def _calculate_max_drawdown(data):
    """Calculate maximum drawdown percentage"""
    cumulative_max = data['close'].cummax()
    drawdown = (data['close'] - cumulative_max) / cumulative_max * 100
    return float(drawdown.min())

def _analyze_volume(data):
    """Analyze trading volume"""
    # Ensure data is a DataFrame and reset index if needed
    if not isinstance(data, pd.DataFrame):
        data = pd.DataFrame(data)
    
    # Ensure timestamp column exists and is in datetime format
    if 'timestamp' in data.columns:
        data['timestamp'] = pd.to_datetime(data['timestamp'])
        data.set_index('timestamp', inplace=True)
    
    # Calculate daily volume trend
    volumes = data['volume']
    volume_trend = 'neutral'
    if len(volumes) > 1:
        volume_change = (volumes.iloc[-1] - volumes.iloc[0]) / volumes.iloc[0]
        volume_trend = 'increasing' if volume_change > 0.1 else \
                       'decreasing' if volume_change < -0.1 else 'neutral'
    
    # Convert volume data to list of dictionaries
    daily_volume = [
        {
            "date": str(data.index[i].date()) if hasattr(data.index[i], 'date') else str(data.index[i]),
            "volume": float(data['volume'].iloc[i])
        } for i in range(len(data))
    ]
    
    return {
        "daily_volume": daily_volume,
        "avg_daily_volume": float(volumes.mean()),
        "volume_trend": volume_trend,
        "max_volume_day": {
            "date": str(data.index[volumes.argmax()].date()) if hasattr(data.index[volumes.argmax()], 'date') else str(data.index[volumes.argmax()]),
            "volume": float(volumes.max())
        }
    }

async def _calculate_correlations(pair: str):
    """
    Calculate correlations with other major cryptocurrencies using actual historical price data
    """
    try:
        # Initialize exchange
        exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot'
            }
        })
        
        # List of major cryptocurrencies to compare
        comparison_pairs = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'XRP/USDT']
        
        # Remove the current pair from comparison if present
        if pair in comparison_pairs:
            comparison_pairs.remove(pair)
        
        # Fetch historical data for all pairs
        correlations = []
        for compare_pair in comparison_pairs:
            try:
                # Fetch historical data
                historical_data = await asyncio.to_thread(
                    CryptoPriceCollector().fetch_historical_data, 
                    compare_pair, 
                    timeframe='1d'  # Use daily data for correlation
                )
                
                # Calculate correlation
                current_pair_data = await asyncio.to_thread(
                    CryptoPriceCollector().fetch_historical_data, 
                    pair, 
                    timeframe='1d'
                )
                
                # Calculate Pearson correlation coefficient
                corr_coef = current_pair_data['close'].corr(historical_data['close'])
                
                # Determine correlation type
                correlation_type = (
                    'positive' if corr_coef > 0.5 else 
                    'negative' if corr_coef < -0.5 else 
                    'neutral'
                )
                
                correlations.append({
                    "asset": compare_pair,
                    "correlation_coefficient": float(corr_coef),
                    "correlation_type": correlation_type
                })
            
            except Exception as e:
                print(f"Error calculating correlation for {compare_pair}: {str(e)}")
        
        return {"correlations": correlations}
    
    except Exception as e:
        print(f"Error in correlation calculation: {str(e)}")
        return {"correlations": []}

def _identify_support_resistance_levels(data):
    """Identify support and resistance levels"""
    if len(data) == 0:
        return {
            "price_history": [],
            "support_levels": [],
            "resistance_levels": [],
            "current_price": 0
        }
    
    # Convert to list of dictionaries for serialization
    price_history = [
        {
            "date": str(data.index[i].date()),
            "price": float(data.iloc[i]['close'])
        } for i in range(len(data))
    ]
    
    # Calculate close prices
    close_prices = data['close']
    
    # Calculate support levels
    support_levels = [
        {
            "level": float(close_prices.rolling(window=20).min().iloc[-1]),
            "strength": 0.7
        },
        {
            "level": float(close_prices.rolling(window=50).min().iloc[-1]),
            "strength": 0.5
        }
    ]
    
    # Calculate resistance levels
    resistance_levels = [
        {
            "level": float(close_prices.rolling(window=20).max().iloc[-1]),
            "strength": 0.7
        },
        {
            "level": float(close_prices.rolling(window=50).max().iloc[-1]),
            "strength": 0.5
        }
    ]
    
    return {
        "price_history": price_history,
        "support_levels": support_levels,
        "resistance_levels": resistance_levels,
        "current_price": float(close_prices.iloc[-1])
    }