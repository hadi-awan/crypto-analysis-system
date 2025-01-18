from typing import Dict, List, Callable, Optional
import pandas as pd
import asyncio
import logging
from app.data_collectors.price_collector import CryptoPriceCollector
from app.data_processors.technical_indicators import TechnicalAnalyzer
from app.services.signals.signal_generator import SignalGenerator, Signal
from app.validation.price_validators import PriceDataValidator
from app.services.signals.signal_filter import SignalFilter, FilterConfig


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
            required_confirmations=2,
            cooldown_period=300,  # 5 minutes
            allowed_indicators=['RSI', 'MACD', 'BB', 'STOCH']
        ))
        self.signal_subscribers: Dict[str, List[Callable]] = {'ALL': []}
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
        try:
            new_data = pd.DataFrame([{
                'timestamp': price_data['timestamp'],
                'close': float(price_data['price']),
                'high': float(price_data.get('high', price_data['price'])),
                'low': float(price_data.get('low', price_data['price'])),
                'volume': float(price_data['volume'])
            }])
            
            # Update data buffer
            self.data_buffer = pd.concat([self.data_buffer, new_data], ignore_index=True)
            if len(self.data_buffer) > self.buffer_size:
                self.data_buffer = self.data_buffer.tail(self.buffer_size)
            
            # Calculate indicators if enough data
            if len(self.data_buffer) >= 14:
                analyzer = TechnicalAnalyzer(self.data_buffer)
                
                # Calculate indicators
                latest_data = pd.DataFrame([{
                    'timestamp': price_data['timestamp'],
                    'close': float(price_data['price']),
                    'volume': float(price_data['volume']),
                    'rsi': float(analyzer.calculate_rsi().iloc[-1]),
                    'macd': float(analyzer.calculate_macd()[0].iloc[-1]),
                    'macd_signal': float(analyzer.calculate_macd()[1].iloc[-1])
                }])
                
                # Add Bollinger Bands
                bb_upper, bb_middle, bb_lower = analyzer.calculate_bollinger_bands()
                latest_data['bb_upper'] = float(bb_upper.iloc[-1])
                latest_data['bb_middle'] = float(bb_middle.iloc[-1])
                latest_data['bb_lower'] = float(bb_lower.iloc[-1])

                # Add Stochastic
                stoch_k, stoch_d = analyzer.calculate_stochastic()
                latest_data['stoch_k'] = float(stoch_k.iloc[-1])
                latest_data['stoch_d'] = float(stoch_d.iloc[-1])
                
                # Update stored indicators
                self.indicators = {
                    'rsi': latest_data['rsi'].iloc[0],
                    'macd': latest_data['macd'].iloc[0],
                    'macd_signal': latest_data['macd_signal'].iloc[0],
                    'bb_upper': latest_data['bb_upper'].iloc[0],
                    'bb_lower': latest_data['bb_lower'].iloc[0],
                    'stoch_k': latest_data['stoch_k'].iloc[0],
                    'stoch_d': latest_data['stoch_d'].iloc[0]
                }

                # Notify indicator subscribers
                for indicator, value in self.indicators.items():
                    if indicator in self.subscribers:
                        for subscriber in self.subscribers[indicator]:
                            try:
                                await subscriber({
                                    'indicator': indicator,
                                    'value': value,
                                    'timestamp': price_data['timestamp']
                                })
                            except Exception as e:
                                self.logger.error(f"Error in indicator callback: {str(e)}")
                
                # Generate signals
                signals = self.signal_generator.generate_signals(latest_data)
                filtered_signals = []
        
                for signal in signals:
                    if self.signal_filter.filter_signal(signal):
                        filtered_signals.append(signal)
                        self.signal_filter.update_recent_signals(signal)
                        await self._notify_signal_subscribers(signal)
                
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
