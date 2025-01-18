# app/services/analysis/realtime_analyzer.py
from typing import Dict, List, Callable, Optional
import pandas as pd
import asyncio
import logging
import uuid
from datetime import datetime
from app.data_collectors.price_collector import CryptoPriceCollector
from app.data_processors.technical_indicators import TechnicalAnalyzer
from app.services.signals.signal_generator import SignalGenerator, Signal
from app.validation.price_validators import PriceDataValidator
from app.services.signals.signal_filter import SignalFilter, FilterConfig
from app.services.performance.performance_tracker import PerformanceTracker

class RealtimeAnalyzer:
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.price_collector = CryptoPriceCollector()
        self.data_buffer = pd.DataFrame()
        self.buffer_size = 100
        self.indicators = {}
        self.signal_generator = SignalGenerator()
        self.signal_filter = SignalFilter(FilterConfig(
            min_strength=0.3,
            required_confirmations=1,  # Reduced for testing
            cooldown_period=1,  # Reduced for testing
            allowed_indicators=['RSI', 'MACD', 'BB', 'STOCH']
        ))
        self.performance_tracker = PerformanceTracker()
        self.signal_subscribers: Dict[str, List[Callable]] = {'ALL': []}
        self.subscribers: Dict[str, List[Callable]] = {}
        self.active_signals: Dict[str, Signal] = {}
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

    async def _notify_signal_subscribers(self, signal: Signal, signal_id: str):
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
        try:
            current_price = float(price_data['price'])
            
            # Update existing signals with new price
            await self._update_active_signals(current_price)

            new_data = pd.DataFrame([{
                'timestamp': price_data['timestamp'],
                'close': current_price,
                'high': float(price_data.get('high', current_price)),
                'low': float(price_data.get('low', current_price)),
                'volume': float(price_data['volume'])
            }])
            
            # Update data buffer
            self.data_buffer = pd.concat([self.data_buffer, new_data], ignore_index=True)
            if len(self.data_buffer) > self.buffer_size:
                self.data_buffer = self.data_buffer.tail(self.buffer_size)
            
            # Calculate indicators if enough data
            if len(self.data_buffer) >= 14:
                analyzer = TechnicalAnalyzer(self.data_buffer)
                
                # Calculate RSI
                rsi_value = float(analyzer.calculate_rsi().iloc[-1])
                macd_line, macd_signal, _ = analyzer.calculate_macd()
                macd_value = float(macd_line.iloc[-1])
                macd_signal_value = float(macd_signal.iloc[-1])
                
                # Calculate all indicators
                latest_data = pd.DataFrame([{
                    'timestamp': price_data['timestamp'],
                    'close': current_price,
                    'high': float(price_data.get('high', current_price)),
                    'low': float(price_data.get('low', current_price)),
                    'volume': float(price_data['volume']),
                    'rsi': rsi_value,
                    'macd': macd_value,
                    'macd_signal': macd_signal_value
                }])

                # Update stored indicators
                self.indicators = {
                    'rsi': rsi_value,
                    'macd': macd_value,
                    'macd_signal': macd_signal_value
                }

                # Notify indicator subscribers
                for indicator, value in self.indicators.items():
                    if indicator in self.subscribers:
                        indicator_data = {
                            'indicator': indicator,
                            'value': value,
                            'timestamp': price_data['timestamp']
                        }
                        for subscriber in self.subscribers[indicator]:
                            try:
                                await subscriber(indicator_data)
                            except Exception as e:
                                self.logger.error(f"Error in indicator callback: {str(e)}")

                # Generate signals only with enough price movement
                if len(self.data_buffer) >= 20:  # Need more data for reliable signals
                    signals = self.signal_generator.generate_signals(latest_data)
                    filtered_signals = []

                    for signal in signals:
                        if self.signal_filter.filter_signal(signal):
                            signal_id = str(uuid.uuid4())
                            filtered_signals.append(signal)
                            
                            # Add to performance tracker with stop loss and take profit
                            self.performance_tracker.add_signal(
                                signal_id=signal_id,
                                signal_type=signal.type.value,
                                indicator=signal.indicator,
                                entry_price=current_price,
                                stop_loss=current_price * 0.95,  # 5% stop loss
                                take_profit=current_price * 1.05  # 5% take profit
                            )
                            
                            # Store active signal
                            self.active_signals[signal_id] = signal
                            
                            # Notify subscribers
                            await self._notify_signal_subscribers(signal, signal_id)

                # Notify callback with all updates
                if callback:
                    metrics = self.performance_tracker.get_performance_metrics()
                    await callback({
                        'price': price_data,
                        'indicators': self.indicators,
                        'signals': signals if 'signals' in locals() else [],
                        'performance': metrics
                    })
                    
        except Exception as e:
            self.logger.error(f"Error processing update: {str(e)}")
            raise

    async def _update_active_signals(self, current_price: float):
        """Update all active signals with new price data"""
        completed_signals = []
        
        for signal_id, signal in list(self.active_signals.items()):
            # Update signal in performance tracker
            result = self.performance_tracker.update_signal(signal_id, current_price)
            
            # If signal is completed, mark for removal
            if result and result.signal_id not in self.performance_tracker.active_signals:
                completed_signals.append(signal_id)
        
        # Remove completed signals
        for signal_id in completed_signals:
            del self.active_signals[signal_id]

    def get_current_performance(self):
        """Get current performance metrics"""
        return self.performance_tracker.get_performance_metrics()