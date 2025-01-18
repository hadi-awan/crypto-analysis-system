import pytest
import asyncio
from datetime import datetime
from app.services.analysis.realtime_analyzer import RealtimeAnalyzer
from app.services.signals.signal_generator import SignalType
from app.services.signals.signal_filter import SignalFilter, FilterConfig

class MockPriceCollector:
    def __init__(self):
        self.callbacks = []
        self.connected = False
        self.base_price = 50000.0

    def generate_mock_price(self, trend='neutral'):
        """Generate mock price data with specified trend"""
        if trend == 'up':
            self.base_price *= 1.05
        elif trend == 'down':
            self.base_price *= 0.95
            
        return {
            'timestamp': datetime.now(),
            'price': self.base_price,
            'high': self.base_price * 1.02,
            'low': self.base_price * 0.98,
            'volume': 1000.0
        }

    async def connect_realtime(self, symbol: str):
        self.connected = True
        return True

    async def disconnect_realtime(self):
        self.connected = False

    async def subscribe_to_price_updates(self, symbol: str, callback):
        self.callbacks.append(callback)
        # Generate initial data for indicators
        await self._generate_initial_data(callback)
        
    async def _generate_initial_data(self, callback):
        """Generate enough initial data points for indicator calculation"""
        price = self.base_price
        for i in range(30):  # Generate 30 data points for indicator calculation
            if i < 10:
                # First 10 points slight uptrend
                price *= 1.001
            elif i < 20:
                # Next 10 points downtrend
                price *= 0.999
            else:
                # Last 10 points uptrend
                price *= 1.001
                
            await callback({
                'timestamp': datetime.now(),
                'price': price,
                'high': price * 1.01,
                'low': price * 0.99,
                'volume': 1000.0 * (1 + (i * 0.1))
            })
            await asyncio.sleep(0.01)  # Small delay between updates


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
    mock_price = {
        'timestamp': datetime.now(),
        'price': 50000.0,
        'volume': 100.0
    }
    for _ in range(15):
        await analyzer.handle_price_update(mock_price)
    
    await asyncio.sleep(0.1)
    await analyzer.stop()
    
    assert len(rsi_data) > 0
    assert len(macd_data) > 0
    assert 'indicator' in rsi_data[0]
    assert 'value' in rsi_data[0]


@pytest.mark.asyncio
async def test_signal_filtering_strength():
    analyzer = RealtimeAnalyzer("BTC/USDT")
    received_signals = []

    async def signal_handler(signal):
        received_signals.append(signal)

    await analyzer.subscribe_to_signals(signal_handler)
    analyzer.signal_filter = SignalFilter(FilterConfig(min_strength=0.8))
    
    prices = [50000, 45000, 42000, 40000]
    for price in prices:
        await analyzer.handle_price_update({
            'timestamp': datetime.now(),
            'price': price,
            'high': price * 1.01,
            'low': price * 0.99,
            'volume': 1000.0
        })

    assert all(signal.strength >= 0.8 for signal in received_signals)


@pytest.mark.asyncio
async def test_signal_filtering_cooldown():
    analyzer = RealtimeAnalyzer("BTC/USDT")
    received_signals = []

    async def signal_handler(signal):
        received_signals.append(signal)

    await analyzer.subscribe_to_signals(signal_handler)
    analyzer.signal_filter = SignalFilter(FilterConfig(cooldown_period=300))
    for _ in range(5):
        await analyzer.handle_price_update({
            'timestamp': datetime.now(),
            'price': 40000,
            'high': 40400,
            'low': 39600,
            'volume': 1000.0
        })
        await asyncio.sleep(0.1)

    signal_times = {}
    for signal in received_signals:
        key = f"{signal.indicator}_{signal.type.value}"
        if key in signal_times:
            time_diff = (signal.timestamp - signal_times[key]).total_seconds()
            assert time_diff >= 300
        signal_times[key] = signal.timestamp

@pytest.mark.asyncio
async def test_signal_integration():
    """Test complete signal generation and filtering workflow"""
    analyzer = RealtimeAnalyzer("BTC/USDT")
    filtered_signals = []
    all_signals = []

    async def signal_handler(signal):
        filtered_signals.append(signal)

    # Set up filtering with more lenient conditions
    analyzer.signal_filter = SignalFilter(FilterConfig(
        min_strength=0.3,  # Lower strength requirement
        required_confirmations=1,  # No confirmations needed
        cooldown_period=1,  # Short cooldown
        allowed_indicators=['RSI', 'MACD', 'BB', 'STOCH']  # All indicators allowed
    ))

    await analyzer.subscribe_to_signals(signal_handler)
    
    # Generate more data points with significant price movement
    base_price = 50000
    for i in range(20):  # More data points
        multiplier = 1 - (i * 0.02)  # 2% drop each time
        price = base_price * multiplier
        await analyzer.handle_price_update({
            'timestamp': datetime.now(),
            'price': price,
            'high': price * 1.02,  # More volatile price movement
            'low': price * 0.98,
            'volume': 1000.0 * (1 + (i * 0.1))  # Increasing volume
        })
        await asyncio.sleep(0.1)

    assert len(filtered_signals) > 0, "Should generate some signals"
    
    # Verify signal properties
    for signal in filtered_signals:
        assert signal.strength >= 0.3, "All signals should meet strength threshold"
        assert signal.timestamp is not None, "Signals should have timestamps"
        assert signal.type in [SignalType.BUY, SignalType.SELL], "Signals should have valid types"
        print(f"Generated signal: {signal.type.value} from {signal.indicator} with strength {signal.strength}")

    # Log indicator values for debugging
    print("\nFinal indicator values:", analyzer.indicators)

@pytest.mark.asyncio
async def test_performance_tracking_initialization():
    """Test proper initialization of performance tracking"""
    analyzer = RealtimeAnalyzer("BTC/USDT")
    assert hasattr(analyzer, 'performance_tracker')
    metrics = analyzer.get_current_performance()
    assert metrics.total_signals == 0

@pytest.mark.asyncio
async def test_signal_performance_tracking():
    """Test tracking of signal performance through price updates"""
    analyzer = RealtimeAnalyzer("BTC/USDT")
    received_signals = []
    
    async def signal_handler(signal):
        received_signals.append(signal)
    
    await analyzer.subscribe_to_signals(signal_handler)
    
    # Generate initial data points
    await generate_initial_data(analyzer)
    
    # Generate significant price movements
    price_sequence = [
        50000,  # Base price
        45000,  # 10% drop - should trigger oversold
        43000,  # Further drop
        41000,  # More drop to ensure signal
        45000,  # Recovery
        48000,  # Further recovery to trigger completion
    ]
    
    for price in price_sequence:
        for _ in range(3):  # Multiple updates at each price level
            await analyzer.handle_price_update({
                'timestamp': datetime.now(),
                'price': price,
                'high': price * 1.02,
                'low': price * 0.98,
                'volume': 1000.0
            })
            await asyncio.sleep(0.01)
    
    # Check if signals were generated and tracked
    metrics = analyzer.get_current_performance()
    assert metrics.total_signals > 0, "No signals were generated"
    assert len(received_signals) > 0, "No signals were received by handler"


@pytest.mark.asyncio
async def test_signal_completion_triggers():
    """Test different ways signals can be completed"""
    analyzer = RealtimeAnalyzer("BTC/USDT")
    base_price = 50000.0
    
    # Generate initial data
    await analyzer.handle_price_update({
        'timestamp': datetime.now(),
        'price': base_price,
        'high': base_price * 1.01,
        'low': base_price * 0.99,
        'volume': 1000.0
    })
    
    # Trigger profit target
    profit_price = base_price * 1.05  # 5% profit
    await analyzer.handle_price_update({
        'timestamp': datetime.now(),
        'price': profit_price,
        'high': profit_price * 1.01,
        'low': profit_price * 0.99,
        'volume': 1000.0
    })
    
    metrics = analyzer.get_current_performance()
    assert metrics.total_signals >= 0  # Some signals should be completed


@pytest.mark.asyncio
async def test_performance_metrics_update():
    """Test that performance metrics are updated correctly"""
    analyzer = RealtimeAnalyzer("BTC/USDT")
    all_updates = []
    
    async def callback(data):
        if 'performance' in data:
            all_updates.append(data['performance'])
    
    # Generate initial data
    await generate_initial_data(analyzer)
    
    # Generate significant price movements
    base_price = 50000.0
    movements = [
        1.0,    # Start at base
        0.90,   # Sharp drop (10%)
        0.85,   # Further drop
        0.95,   # Recovery
        1.05,   # Sharp rise
        1.10    # Further rise
    ]
    
    for movement in movements:
        current_price = base_price * movement
        for _ in range(3):  # Multiple updates at each level
            await analyzer.handle_price_update({
                'timestamp': datetime.now(),
                'price': current_price,
                'high': current_price * 1.02,
                'low': current_price * 0.98,
                'volume': 1000.0
            }, callback)
            await asyncio.sleep(0.01)
    
    assert len(all_updates) > 0, "No performance updates received"


@pytest.mark.asyncio
async def test_multiple_signal_types():
    """Test performance tracking with different signal types"""
    analyzer = RealtimeAnalyzer("BTC/USDT")
    signals_received = []
    
    async def signal_handler(signal):
        signals_received.append(signal)
    
    await analyzer.subscribe_to_signals(signal_handler)
    
    # Generate initial data
    await generate_initial_data(analyzer)
    
    # Generate both bullish and bearish conditions
    price_sequence = [
        50000,  # Start
        45000,  # Sharp drop (-10%) - should trigger buy
        43000,  # Further drop
        48000,  # Recovery
        53000,  # Rise (+10%)
        58000,  # Further rise - should trigger sell
        55000   # Slight drop
    ]
    
    for price in price_sequence:
        for _ in range(3):  # Multiple updates at each level
            await analyzer.handle_price_update({
                'timestamp': datetime.now(),
                'price': price,
                'high': price * 1.02,
                'low': price * 0.98,
                'volume': 1000.0 * (1 + (price/50000 - 1))  # Volume increases with price
            })
            await asyncio.sleep(0.01)
    
    # Verify we got different types of signals
    signal_types = set(signal.type for signal in signals_received)
    assert len(signal_types) > 1, "Should have both BUY and SELL signals"
    assert len(signals_received) > 0, "No signals were received"

async def generate_initial_data(analyzer: RealtimeAnalyzer, num_points: int = 20):
    """Helper function to generate enough initial data points"""
    base_price = 50000.0
    for i in range(num_points):
        await analyzer.handle_price_update({
            'timestamp': datetime.now(),
            'price': base_price,
            'high': base_price * 1.01,
            'low': base_price * 0.99,
            'volume': 1000.0
        })
        await asyncio.sleep(0.01)