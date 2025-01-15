# tests/services/analysis/test_realtime_analyzer.py
import pytest
import asyncio
import pandas as pd
from datetime import datetime
from app.services.analysis.realtime_analyzer import RealtimeAnalyzer

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
        # Simulate some price updates
        for i in range(20):
            await callback({
                'timestamp': datetime.now(),
                'price': 50000 + i * 100,
                'volume': 1000 + i * 10
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
    await asyncio.sleep(0.1)  # Short wait for mock data
    await analyzer.stop()
    
    assert len(received_data) > 0
    assert 'indicators' in received_data[0]
    assert 'rsi' in received_data[0]['indicators']

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
    await asyncio.sleep(0.1)  # Short wait for mock data
    await analyzer.stop()
    
    assert len(rsi_data) > 0
    assert len(macd_data) > 0