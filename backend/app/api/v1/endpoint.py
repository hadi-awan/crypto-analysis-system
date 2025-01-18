from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.shared.database import get_db
from app.data_collectors.price_collector import CryptoPriceCollector
from app.data_processors.technical_indicators import TechnicalAnalyzer
from pydantic import BaseModel
import asyncio

router = APIRouter(prefix="/api/v1")

class PriceResponse(BaseModel):
    price: float
    timestamp: datetime

class HistoricalDataPoint(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

class HistoricalDataResponse(BaseModel):
    pair: str
    timeframe: str
    data: List[HistoricalDataPoint]

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@router.get("/crypto/price/{pair}", response_model=PriceResponse)
async def get_crypto_price(pair: str):
    """Get current price for a crypto pair"""
    try:
        collector = CryptoPriceCollector()
        normalized_pair = pair.replace("-", "/").upper()
        price_data = await collector.get_current_price(normalized_pair)
        return price_data
    except ValueError:
        raise HTTPException(
            status_code=404,
            detail=f"Crypto pair {pair} not found"
        )

@router.get("/crypto/pairs")
async def get_crypto_pairs():
    """Get available crypto pairs"""
    pairs = ["BTC/USDT", "ETH/USDT", "BTC/EUR"]  # Example pairs, you can modify as needed
    return {"pairs": pairs}
    
@router.websocket("/crypto/ws/{pair}")
async def websocket_endpoint(websocket: WebSocket, pair: str):
    await websocket.accept()
    
    try:
        collector = CryptoPriceCollector()  # Initialize your price collector here
        normalized_pair = pair.replace("-", "/").upper()  # Normalize pair
        
        while True:
            # Fetch real-time price for the pair
            price_data = await collector.get_current_price(normalized_pair)
            
            # Send the data to the client
            await websocket.send_json({
                "price": price_data["price"],  # Assuming price_data is a dict
                "timestamp": datetime.now().isoformat()  # ISO 8601 string format
            })
            
            # Sleep before sending the next update (adjust as needed)
            await asyncio.sleep(1)  # You can adjust the delay for updates as needed
    
    except WebSocketDisconnect:
        print(f"Client disconnected from {pair} WebSocket")
    
    except Exception as e:
        print(f"Error occurred: {e}")
    
    finally:
        await websocket.close()

@router.get("/crypto/historical/{pair}", response_model=HistoricalDataResponse)
async def get_historical_data(
    pair: str,
    timeframe: str = Query("1h", regex="^(1m|5m|15m|1h|4h|1d)$"),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get historical price data"""
    try:
        collector = CryptoPriceCollector()
        normalized_pair = pair.replace("-", "/").upper()
        data = collector.fetch_historical_data(
            normalized_pair,
            timeframe=timeframe,
            limit=limit
        )

        data = data.to_dict(orient='records')
        
        # Ensure that the data is formatted as a list of dictionaries matching HistoricalDataPoint schema
        formatted_data = [
            HistoricalDataPoint(
                timestamp=entry['timestamp'],
                open=entry['open'],
                high=entry['high'],
                low=entry['low'],
                close=entry['close'],
                volume=entry['volume']
            ) for entry in data
        ]
        
        return {
            "pair": normalized_pair,
            "timeframe": timeframe,
            "data": formatted_data
        }
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    
@router.get("/crypto/indicators/{pair}")
async def get_indicators(
    pair: str,
    indicators: str = Query(..., description="Comma-separated list of indicators")
):
    """Get technical indicators for a crypto pair"""
    try:
        collector = CryptoPriceCollector()
        normalized_pair = pair.replace("-", "/").upper()
        
        # Get historical data for indicator calculation
        data = collector.fetch_historical_data(normalized_pair)
        analyzer = TechnicalAnalyzer(data)
        
        # Calculate requested indicators
        result = {}
        indicator_list = [i.strip().lower() for i in indicators.split(",")]
        
        if "rsi" in indicator_list:
            result["rsi"] = float(analyzer.calculate_rsi().iloc[-1])
        
        if "macd" in indicator_list:
            macd_line, signal, hist = analyzer.calculate_macd()
            result["macd"] = {
                "macd": float(macd_line.iloc[-1]),
                "signal": float(signal.iloc[-1]),
                "histogram": float(hist.iloc[-1])
            }
            
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )