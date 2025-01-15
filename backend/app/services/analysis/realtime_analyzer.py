# app/services/analysis/realtime_analyzer.py
import logging
import asyncio
import pandas as pd
from typing import Dict, Callable, Optional
from app.data_collectors.price_collector import CryptoPriceCollector
from app.data_processors.technical_indicators import TechnicalAnalyzer

class RealtimeAnalyzer:
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.price_collector = CryptoPriceCollector()
        self.data_buffer = pd.DataFrame()
        self.buffer_size = 100
        self.indicators = {}  # Store current indicator values
        self.subscribers = {}
        self.running = False
        self.logger = logging.getLogger(__name__)

    async def start(self, callback: Optional[Callable] = None):
        """Start real-time analysis"""
        self.running = True
        await self.price_collector.connect_realtime(self.symbol)
        await self.price_collector.subscribe_to_price_updates(
            self.symbol,
            lambda price_data: self._handle_price_update(price_data, callback)
        )

    async def stop(self):
        """Stop real-time analysis"""
        self.running = False
        await self.price_collector.disconnect_realtime()

    async def subscribe_to_indicator(self, indicator: str, callback: Callable):
        """Subscribe to updates for a specific indicator"""
        self.subscribers[indicator] = callback

    async def _handle_price_update(self, price_data: Dict, callback: Optional[Callable] = None):
        """Handle new price data and calculate indicators"""
        try:
            # Convert single price update to DataFrame row
            new_data = pd.DataFrame([{
                'timestamp': price_data['timestamp'],
                'close': float(price_data['price']),
                'volume': float(price_data['volume'])
            }])
            
            # Append to buffer
            self.data_buffer = pd.concat([self.data_buffer, new_data], ignore_index=True)
            if len(self.data_buffer) > self.buffer_size:
                self.data_buffer = self.data_buffer.tail(self.buffer_size)
            
            # Calculate indicators if we have enough data
            if len(self.data_buffer) >= 14:
                analyzer = TechnicalAnalyzer(self.data_buffer)
                
                # Update indicators
                self.indicators = {
                    'rsi': float(analyzer.calculate_rsi().iloc[-1]),
                    'macd': float(analyzer.calculate_macd()[0].iloc[-1]),
                    'bollinger_bands': [float(bb.iloc[-1]) for bb in analyzer.calculate_bollinger_bands()]
                }
                
                # Notify specific indicator subscribers
                for indicator, value in self.indicators.items():
                    if indicator in self.subscribers:
                        await self.subscribers[indicator]({
                            'indicator': indicator,
                            'value': value,
                            'timestamp': price_data['timestamp']
                        })
                
                # Notify general callback if provided
                if callback:
                    await callback({
                        'price': price_data,
                        'indicators': self.indicators
                    })
                    
        except Exception as e:
            self.logger.error(f"Error processing update: {str(e)}")
            raise  # Re-raise the exception for better error tracking in tests