
# scripts/test_signal_generation.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import pandas as pd
from datetime import datetime, timedelta
from app.data_collectors.price_collector import CryptoPriceCollector
from app.data_processors.technical_indicators import TechnicalAnalyzer
from app.services.signals.signal_generator import SignalGenerator

async def main():
    print("Fetching historical data...")
    collector = CryptoPriceCollector()
    df = collector.fetch_historical_data(
        symbol="BTC/USDT",
        timeframe="1h",
        start_time=datetime.now() - timedelta(days=7)
    )
    
    print("\nCalculating indicators...")
    analyzer = TechnicalAnalyzer(df)
    
    # Calculate and add all required indicators
    df['rsi'] = analyzer.calculate_rsi()
    macd, signal, _ = analyzer.calculate_macd()
    df['macd'] = macd
    df['macd_signal'] = signal
    upper, middle, lower = analyzer.calculate_bollinger_bands()
    df['upper_band'] = upper
    df['middle_band'] = middle
    df['lower_band'] = lower
    
    # Generate signals for the latest data point
    print("\nGenerating signals...")
    signal_generator = SignalGenerator()
    latest_data = df.iloc[-1:].copy()
    signals = signal_generator.generate_signals(latest_data)
    
    # Print current market conditions
    print("\n=== Current Market Conditions ===")
    print(f"Price: ${latest_data['close'].iloc[0]:.2f}")
    print(f"RSI: {latest_data['rsi'].iloc[0]:.2f}")
    print(f"MACD: {latest_data['macd'].iloc[0]:.2f}")
    print(f"MACD Signal: {latest_data['macd_signal'].iloc[0]:.2f}")
    
    # Print signals
    print("\n=== Current Signals ===")
    if not signals:
        print("No signals generated")
    else:
        for signal in signals:
            print(f"\nSignal Type: {signal.type.value}")
            print(f"Indicator: {signal.indicator}")
            print(f"Strength: {signal.strength:.2f}")
            print(f"Message: {signal.message}")
            print(f"Timestamp: {signal.timestamp}")

if __name__ == "__main__":
    asyncio.run(main())
