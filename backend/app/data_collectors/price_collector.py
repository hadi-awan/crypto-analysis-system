# app/data_collectors/price_collector.py
import ccxt.async_support as ccxt_async
import websockets
import asyncio
import json
from datetime import datetime
from typing import Callable, Dict, Optional
import logging

class CryptoPriceCollector:
    def __init__(self, exchange_id: str = 'binance'):
        self.exchange_id = exchange_id
        self.exchange = getattr(ccxt_async, exchange_id)()
        self.ws = None
        self.subscribers: Dict[str, list[Callable]] = {}
        self.running = False
        self.logger = logging.getLogger(__name__)

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