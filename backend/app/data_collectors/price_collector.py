import ccxt
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Callable
import logging
import websockets
import asyncio
import json
from app.validation.price_validators import PriceDataValidator


class CryptoPriceCollector:
    def __init__(self, exchange_id: str = 'binance'):
        self.exchange_id = exchange_id
        self.exchange = getattr(ccxt, exchange_id)()
        self.ws = None
        self.subscribers = {}
        self.running = False
        self.logger = logging.getLogger(__name__)
        self.supported_timeframes = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d']

    def get_supported_timeframes(self) -> List[str]:
        """Get list of supported timeframes"""
        return self.supported_timeframes
    
    def fetch_historical_data(self, symbol: str, timeframe: str = '1m') -> pd.DataFrame:
        """
        Fetch historical price data for a given symbol and timeframe.
        
        For timeframe:
        - 1h: fetch 1-minute candles for the last hour (60 candles)
        - 4h: fetch 5-minute candles for the last 4 hours (48 candles)
        - 1d: fetch 15-minute candles for the last day (96 candles)
        """
        timeframe_settings = {
            '1h': {'interval': '1m', 'limit': 60},    # 1 min candles for 1 hour
            '4h': {'interval': '5m', 'limit': 48},    # 5 min candles for 4 hours
            '1d': {'interval': '15m', 'limit': 96},   # 15 min candles for 1 day
        }
        
        if timeframe not in timeframe_settings:
            raise ValueError(f"Unsupported timeframe. Must be one of: {', '.join(timeframe_settings.keys())}")
            
        exchange_symbol = symbol.replace('/', '').upper()
        settings = timeframe_settings[timeframe]
        
        ohlcv = self.exchange.fetch_ohlcv(
            exchange_symbol,
            timeframe=settings['interval'],
            limit=settings['limit']
        )

        df = pd.DataFrame(
            ohlcv,
            columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
        )
            
        # Convert timestamp to datetime and set to Eastern Time
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms').dt.tz_localize('UTC').dt.tz_convert('America/Toronto')
            
        return df
                

    async def connect_realtime(self, symbol: Optional[str] = None) -> bool:
        """Connect to exchange websocket for real-time data"""
        try:
            if self.exchange_id == 'binance':
                self.ws = await websockets.connect(
                    'wss://stream.binance.com:9443/ws/!ticker@arr'  # Subscribe to all tickers
                )
                self.running = True
                # Start listening for messages
                asyncio.create_task(self._listen_to_stream())
                return True
        except Exception as e:
            self.logger.error(f"WebSocket connection failed: {str(e)}")
            return False

    async def subscribe_to_price_updates(self, symbol: str, callback: Callable):
        """Subscribe to real-time price updates for a symbol"""
        symbol = symbol.replace('/', '').lower()  # Convert BTC/USDT to btcusdt
        if symbol not in self.subscribers:
            self.subscribers[symbol] = []
        self.subscribers[symbol].append(callback)
        self.logger.info(f"Subscribed to updates for {symbol}")

    async def _listen_to_stream(self):
        """Listen to websocket stream and process messages"""
        while self.running and self.ws:
            try:
                message = await self.ws.recv()
                data = json.loads(message)
                
                # Process ticker data
                if isinstance(data, list):  # We're receiving array of all tickers
                    for ticker in data:
                        symbol = ticker['s'].lower()  # Symbol from ticker
                        if symbol in self.subscribers:
                            price_data = {
                                'symbol': ticker['s'],
                                'price': float(ticker['c']),  # Current price
                                'volume': float(ticker['v']),  # Volume
                                'timestamp': datetime.now(),
                                'high': float(ticker['h']),
                                'low': float(ticker['l'])
                            }
                            
                            # Notify all subscribers for this symbol
                            for callback in self.subscribers[symbol]:
                                try:
                                    await callback(price_data)
                                except Exception as e:
                                    self.logger.error(f"Error in callback: {str(e)}")
                
            except websockets.ConnectionClosed:
                self.logger.warning("WebSocket connection closed")
                await self.reconnect()
            except Exception as e:
                self.logger.error(f"Error in WebSocket stream: {str(e)}")
                await asyncio.sleep(1)

    async def reconnect(self):
        """Attempt to reconnect to WebSocket"""
        if not self.running:
            return
            
        try:
            await self.connect_realtime()
        except Exception as e:
            self.logger.error(f"Reconnection failed: {str(e)}")
            await asyncio.sleep(5)

    async def disconnect_realtime(self):
        """Disconnect from websocket"""
        self.running = False
        if self.ws:
            await self.ws.close()
            self.ws = None
    
    async def _process_price_data(self, raw_data: Dict) -> Optional[Dict]:
        """Process and validate price data before sending to subscribers"""
        try:
            price_data = {
                'symbol': raw_data['s'],
                'price': float(raw_data['c']),
                'volume': float(raw_data['v']),
                'timestamp': datetime.now(),
            }
            
            validator = PriceDataValidator()
            result = validator.validate_price_data(price_data)
            
            if not result.is_valid:
                self.logger.warning(f"Invalid price data: {result.errors}")
                return None
                
            return result.validated_data
            
        except Exception as e:
            self.logger.error(f"Error processing price data: {str(e)}")
            return None

    async def _listen_to_stream(self):
        while self.running and self.ws:
            try:
                message = await self.ws.recv()
                data = json.loads(message)
                
                if isinstance(data, list):
                    for ticker in data:
                        validated_data = await self._process_price_data(ticker)
                        if validated_data:
                            symbol = validated_data['symbol'].lower()
                            if symbol in self.subscribers:
                                for callback in self.subscribers[symbol]:
                                    await callback(validated_data)
                        
            except websockets.ConnectionClosed:
                self.logger.warning("WebSocket connection closed")
                await self.reconnect()
            except Exception as e:
                self.logger.error(f"Error in WebSocket stream: {str(e)}")
                await asyncio.sleep(1)

    async def get_current_price(self, symbol: str) -> Dict:
        """Get the current price for a symbol"""
        try:
            symbol = symbol.replace('/', '').upper()  # Normalize symbol format
            ticker = self.exchange.fetch_ticker(symbol)  # Get current ticker info
            price_data = {
                'price': ticker['last'],  # Last trade price
                'timestamp': datetime.now()
            }
            return price_data
        except ccxt.ExchangeError as e:
            if "symbol" in str(e).lower():
                raise ValueError(f"Invalid symbol: {symbol}")
            raise e