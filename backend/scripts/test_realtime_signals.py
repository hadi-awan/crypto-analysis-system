import sys
import os
import asyncio
import logging
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the necessary classes
from app.services.analysis.realtime_analyzer import RealtimeAnalyzer
from app.validation.price_validators import PriceDataValidator, ValidationErrorCode

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create a mock signal class for testing purposes (if not already defined in your codebase)
class Signal:
    def __init__(self, symbol, price, volume, timestamp):
        self.symbol = symbol
        self.price = price
        self.volume = volume
        self.timestamp = timestamp

# Define the signal handler function
async def signal_handler(signal):
    logger.info("\n=== New Signal ===")
    logger.info(f"Symbol: {signal.symbol}")  # Log the symbol to check if it's in the correct format
    logger.info(f"Price: {signal.price}")
    logger.info(f"Volume: {signal.volume}")
    logger.info(f"Time: {signal.timestamp}")
    
    # Strip any whitespace or unexpected characters in the symbol
    stripped_symbol = signal.symbol.strip()
    logger.debug(f"Stripped Symbol: {stripped_symbol}")  # Log the stripped symbol for debugging
    
    # Validation of the signal symbol format
    validator = PriceDataValidator()
    result = validator.validate_price_data({
        'symbol': stripped_symbol,  # Pass the stripped symbol for validation
        'price': signal.price,
        'volume': signal.volume,
        'timestamp': signal.timestamp
    })
    
    # If invalid symbol format, log errors
    if not result.is_valid:
        logger.error(f"Invalid price data: {result.errors}")

# Main function to start the analyzer
async def main():
    # Create an instance of RealtimeAnalyzer with a valid symbol
    analyzer = RealtimeAnalyzer("BTC/USDT")  # Assuming this symbol is valid
    
    # Subscribe to all signals (this will trigger the signal_handler)
    await analyzer.subscribe_to_signals(signal_handler)
    
    logger.info("Starting real-time analysis...")
    await analyzer.start()

    # Test: Manually sending a signal for testing purposes
    test_signal = Signal(symbol="BTC/USDT", price=50000.0, volume=1.5, timestamp=datetime.now())
    await signal_handler(test_signal)  # Directly test the signal handler
    
    try:
        while True:
            await asyncio.sleep(1)  # Keep the event loop running
    except KeyboardInterrupt:
        logger.info("\nShutting down...")
    finally:
        await analyzer.stop()

if __name__ == "__main__":
    # Run the main function asynchronously
    asyncio.run(main())
