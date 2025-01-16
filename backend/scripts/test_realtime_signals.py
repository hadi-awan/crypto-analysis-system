# scripts/test_realtime_signals.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from app.services.analysis.realtime_analyzer import RealtimeAnalyzer

async def signal_handler(signal):
    print(f"\n=== New Signal ===")
    print(f"Type: {signal.type.value}")
    print(f"Indicator: {signal.indicator}")
    print(f"Strength: {signal.strength:.2f}")
    print(f"Message: {signal.message}")
    print(f"Time: {signal.timestamp}")

async def main():
    analyzer = RealtimeAnalyzer("BTC/USDT")
    
    # Subscribe to all signals
    await analyzer.subscribe_to_signals(signal_handler)
    
    print("Starting real-time analysis...")
    await analyzer.start()
    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        await analyzer.stop()

if __name__ == "__main__":
    asyncio.run(main())