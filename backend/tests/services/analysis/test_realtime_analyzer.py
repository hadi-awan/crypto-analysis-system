import pytest
import asyncio
from datetime import datetime
from app.services.analysis.realtime_analyzer import RealtimeAnalyzer
from app.services.signals.signal_generator import SignalType

class MockPriceCollector:
    def __init__(self):
        self.callbacks = []
        self.connected = False

    async def connect_realtime(self, symbol: str):
        self.connected = True
        return True

    async def disconnect_realtime(self):
        self.connected = False

    async def subscribe_to_price_updates(self, symbol: str, callback):
        self.callbacks.append(callback)
        # Simulate enough price updates to generate indicators
        for i in range(15):  # Need at least 14 points for indicators
            await callback({
                'timestamp': datetime.now(),
                'price': 50000.0 + (i * 100),  # Add some price movement
                'volume': 1000.0 + (i * 10)
            })

@pytest.fixture
def mock_price_collector(monkeypatch):
    collector = MockPriceCollector()
    monkeypatch.setattr("app.services.analysis.realtime_analyzer.CryptoPriceCollector", 
                       lambda: collector)
    return collector

@pytest.mark.asyncio
async def test_realtime_analyzer_initialization():
    analyzer = RealtimeAnalyzer("BTC/USDT")
    assert analyzer.symbol == "BTC/USDT"
    assert hasattr(analyzer, 'price_collector')
    assert hasattr(analyzer, 'indicators')

@pytest.mark.asyncio
async def test_realtime_indicator_calculation(mock_price_collector):
    analyzer = RealtimeAnalyzer("BTC/USDT")
    received_data = []
    
    async def indicator_handler(data):
        received_data.append(data)
    
    await analyzer.start(indicator_handler)
    await asyncio.sleep(0.1)
    await analyzer.stop()
    
    assert len(received_data) > 0
    assert 'indicators' in received_data[0]
    assert 'price' in received_data[0]

@pytest.mark.asyncio
async def test_multiple_indicator_subscriptions(mock_price_collector):
    analyzer = RealtimeAnalyzer("BTC/USDT")
    rsi_data = []
    macd_data = []
    
    async def rsi_handler(data):
        rsi_data.append(data)
        
    async def macd_handler(data):
        macd_data.append(data)
    
    await analyzer.subscribe_to_indicator('rsi', rsi_handler)
    await analyzer.subscribe_to_indicator('macd', macd_handler)
    
    await analyzer.start()
    
    # Simulate some price updates
    mock_price = {
        'timestamp': datetime.now(),
        'price': 50000.0,
        'volume': 100.0
    }
    
    # Send enough updates to generate indicators
    for _ in range(15):  # Need at least 14 data points for indicators
        await analyzer.handle_price_update(mock_price)
    
    await asyncio.sleep(0.1)
    await analyzer.stop()
    
    assert len(rsi_data) > 0, "Should receive RSI updates"
    assert len(macd_data) > 0, "Should receive MACD updates"
    
    # Verify data structure
    assert 'indicator' in rsi_data[0]
    assert 'value' in rsi_data[0]
    assert rsi_data[0]['indicator'] == 'rsi'
    assert macd_data[0]['indicator'] == 'macd'

@pytest.mark.asyncio
async def test_signal_generation_integration(mock_price_collector):
    analyzer = RealtimeAnalyzer("BTC/USDT")
    received_signals = []
    
    async def signal_handler(signal):
        received_signals.append(signal)
    
    await analyzer.subscribe_to_signals(signal_handler)
    await analyzer.start()
    await asyncio.sleep(0.1)  # Wait for mock data
    await analyzer.stop()
    
    assert len(received_signals) > 0
    assert hasattr(received_signals[0], 'type')
    assert isinstance(received_signals[0].type, SignalType)

@pytest.mark.asyncio
async def test_specific_signal_subscription(mock_price_collector):
    analyzer = RealtimeAnalyzer("BTC/USDT")
    rsi_signals = []
    macd_signals = []
    
    async def rsi_handler(signal):
        if signal.indicator == 'RSI':
            rsi_signals.append(signal)
            
    async def macd_handler(signal):
        if signal.indicator == 'MACD':
            macd_signals.append(signal)
    
    await analyzer.subscribe_to_signals(rsi_handler, indicators=['RSI'])
    await analyzer.subscribe_to_signals(macd_handler, indicators=['MACD'])
    
    await analyzer.start()
    await asyncio.sleep(0.1)
    await analyzer.stop()
    
    # Each handler should only receive its specific signals
    assert all(signal.indicator == 'RSI' for signal in rsi_signals)
    assert all(signal.indicator == 'MACD' for signal in macd_signals)