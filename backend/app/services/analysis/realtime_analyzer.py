# app/services/analysis/realtime_analyzer.py
from typing import Dict, List, Callable, Optional
import pandas as pd
import asyncio
import logging
from app.data_collectors.price_collector import CryptoPriceCollector
from app.data_processors.technical_indicators import TechnicalAnalyzer
from app.services.signals.signal_generator import SignalGenerator, Signal

class RealtimeAnalyzer:
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.price_collector = CryptoPriceCollector()
        self.data_buffer = pd.DataFrame()
        self.buffer_size = 100
        self.indicators = {}
        self.signal_generator = SignalGenerator()
        self.signal_subscribers: Dict[str, List[Callable]] = {
            'ALL': []  # Subscribers that want all signals
        }
        self.subscribers: Dict[str, List[Callable]] = {}
        self.running = False
        self.logger = logging.getLogger(__name__)

    async def start(self, callback: Optional[Callable] = None):
        """Start real-time analysis"""
        self.running = True
        await self.price_collector.connect_realtime(self.symbol)
        await self.price_collector.subscribe_to_price_updates(
            self.symbol,
            lambda price_data: self.handle_price_update(price_data, callback)
        )

    async def stop(self):
        """Stop real-time analysis"""
        self.running = False
        await self.price_collector.disconnect_realtime()

    async def subscribe_to_indicator(self, indicator: str, callback: Callable):
        """Subscribe to updates for a specific indicator"""
        if indicator not in self.subscribers:
            self.subscribers[indicator] = []
        self.subscribers[indicator].append(callback)

    async def subscribe_to_signals(self, callback: Callable[[Signal], None], indicators: Optional[List[str]] = None):
        """Subscribe to specific or all signal types"""
        if indicators is None:
            self.signal_subscribers['ALL'].append(callback)
        else:
            for indicator in indicators:
                if indicator not in self.signal_subscribers:
                    self.signal_subscribers[indicator] = []
                self.signal_subscribers[indicator].append(callback)

    async def _notify_signal_subscribers(self, signal: Signal):
        """Notify relevant subscribers of new signals"""
        # Notify specific indicator subscribers
        if signal.indicator in self.signal_subscribers:
            for callback in self.signal_subscribers[signal.indicator]:
                try:
                    await callback(signal)
                except Exception as e:
                    self.logger.error(f"Error in signal callback: {str(e)}")

        # Notify subscribers who want all signals
        for callback in self.signal_subscribers['ALL']:
            try:
                await callback(signal)
            except Exception as e:
                self.logger.error(f"Error in signal callback: {str(e)}")

    async def handle_price_update(self, price_data: Dict, callback: Optional[Callable] = None):
        """Handle new price data, calculate indicators and generate signals"""
        try:
            new_data = pd.DataFrame([{
                'timestamp': price_data['timestamp'],
                'close': float(price_data['price']),
                'volume': float(price_data['volume'])
            }])
            
            # Update data buffer
            self.data_buffer = pd.concat([self.data_buffer, new_data], ignore_index=True)
            if len(self.data_buffer) > self.buffer_size:
                self.data_buffer = self.data_buffer.tail(self.buffer_size)
            
            # Calculate indicators if enough data
            if len(self.data_buffer) >= 14:
                analyzer = TechnicalAnalyzer(self.data_buffer)
                
                # Calculate all required indicators
                latest_data = self.data_buffer.iloc[-1:].copy()
                latest_data['rsi'] = analyzer.calculate_rsi().iloc[-1]
                macd, signal, _ = analyzer.calculate_macd()
                latest_data['macd'] = macd.iloc[-1]
                latest_data['macd_signal'] = signal.iloc[-1]
                upper, middle, lower = analyzer.calculate_bollinger_bands()
                latest_data['upper_band'] = upper.iloc[-1]
                latest_data['middle_band'] = middle.iloc[-1]
                latest_data['lower_band'] = lower.iloc[-1]
                
                # Notify indicator subscribers
                for indicator, value in {
                    'rsi': float(latest_data['rsi']),
                    'macd': float(latest_data['macd'])
                }.items():
                    if indicator in self.subscribers:
                        for callback in self.subscribers[indicator]:
                            await callback({
                                'indicator': indicator,
                                'value': value
                            })
                
                # Generate and notify signals
                signals = self.signal_generator.generate_signals(latest_data)
                for signal in signals:
                    await self._notify_signal_subscribers(signal)
                
                # Update stored indicators
                self.indicators = {
                    'rsi': float(latest_data['rsi']),
                    'macd': float(latest_data['macd']),
                    'macd_signal': float(latest_data['macd_signal']),
                    'bb_upper': float(latest_data['upper_band']),
                    'bb_lower': float(latest_data['lower_band'])
                }
                
                # Notify general callback if provided
                if callback:
                    await callback({
                        'price': price_data,
                        'indicators': self.indicators,
                        'signals': signals
                    })
                    
        except Exception as e:
            self.logger.error(f"Error processing update: {str(e)}")
            raise