# tests/data_collectors/test_realtime_collector.py
import pytest
import asyncio
from app.data_collectors.price_collector import CryptoPriceCollector

pytestmark = pytest.mark.asyncio

@pytest.fixture
async def collector():
    collector = CryptoPriceCollector()
    yield collector
    await collector.disconnect_realtime()

async def test_realtime_price_connection(collector):
    connected = await collector.connect_realtime()
    assert connected is True
    await asyncio.sleep(1)

async def test_realtime_price_updates(collector):
    received_data = []
    test_complete = asyncio.Event()
    
    async def price_handler(price_data):
        received_data.append(price_data)
        if len(received_data) > 0:
            test_complete.set()
    
    await collector.connect_realtime()
    await collector.subscribe_to_price_updates("BTC/USDT", price_handler)
    
    try:
        # Wait for data or timeout after 15 seconds
        await asyncio.wait_for(test_complete.wait(), timeout=15)
    except asyncio.TimeoutError:
        pytest.fail("Timeout waiting for price updates")

    assert len(received_data) > 0
    assert 'price' in received_data[0]
    assert 'timestamp' in received_data[0]
    assert isinstance(received_data[0]['price'], float)

async def test_multiple_symbols(collector):
    symbols = ["BTC/USDT", "ETH/USDT"]
    received_data = {symbol: [] for symbol in symbols}
    test_complete = asyncio.Event()
    
    async def create_handler(symbol):
        async def handler(price_data):
            received_data[symbol].append(price_data)
            if all(len(data) > 0 for data in received_data.values()):
                test_complete.set()
        return handler
    
    await collector.connect_realtime()
    
    for symbol in symbols:
        handler = await create_handler(symbol)
        await collector.subscribe_to_price_updates(symbol, handler)
    
    try:
        # Wait for data or timeout after 15 seconds
        await asyncio.wait_for(test_complete.wait(), timeout=15)
    except asyncio.TimeoutError:
        pytest.fail("Timeout waiting for price updates")

    for symbol in symbols:
        assert len(received_data[symbol]) > 0
        assert isinstance(received_data[symbol][0]['price'], float)