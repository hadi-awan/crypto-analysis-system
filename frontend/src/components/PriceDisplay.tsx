import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface PriceData {
  price: number;
  timestamp: string;
  openPrice: number | null;
  dailyChange: number | null;
}

interface PriceDisplayProps {
  symbol?: string;
}

interface HistoricalDataPoint {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface HistoricalDataResponse {
  pair: string;
  timeframe: string;
  data: HistoricalDataPoint[];
}

interface CurrentPriceResponse {
  price: number;
  timestamp: string;
}

function PriceDisplay({ symbol = 'BTC-USDT' }: PriceDisplayProps) {
  const [price, setPrice] = useState<PriceData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isConnecting, setIsConnecting] = useState(true);
  const [ws, setWs] = useState<WebSocket | null>(null);

  // Get daily opening price
  const fetchOpenPrice = async () => {
    try {
      const response = await axios.get<HistoricalDataResponse>(
        `http://localhost:8000/api/v1/crypto/historical/${symbol}`,
        {
          params: {
            timeframe: '1d'  // Get daily data
          }
        }
      );
      
      if (response.data.data && response.data.data.length > 0) {
        return response.data.data[0].open; // Get today's opening price
      }
      return null;
    } catch (error) {
      console.error('Error fetching opening price:', error);
      return null;
    }
  };

  const getPriceChangeClass = (change: number) => {
    if (change === 0) return 'text-gray-500';
    return change > 0 ? 'text-green-500' : 'text-red-500';
  };

  const formatPriceChange = (change: number) => {
    const sign = change > 0 ? '+' : '';
    return `${sign}${change.toFixed(2)}%`;
  };

  // Fetch initial price and set up WebSocket
  useEffect(() => {
    let openPrice: number | null = null;

    const initialize = async () => {
      try {
        // Fetch opening price first
        openPrice = await fetchOpenPrice();
        
        // Fetch current price
        const response = await axios.get<CurrentPriceResponse>(
          `http://localhost:8000/api/v1/crypto/price/${symbol}`
        );
        
        const dailyChange = openPrice ? 
          ((response.data.price - openPrice) / openPrice) * 100 : 
          0;

        const initialPriceData: PriceData = {
          price: response.data.price,
          timestamp: response.data.timestamp,
          openPrice: openPrice,
          dailyChange: dailyChange
        };
        
        setPrice(initialPriceData);
        setIsConnecting(false);
      } catch (error) {
        console.error('Error fetching initial data:', error);
        setError('Failed to fetch initial price');
        setIsConnecting(false);
      }
    };

    // Set up WebSocket connection
    const connectWebSocket = () => {
      const wsUrl = `ws://127.0.0.1:8000/api/v1/crypto/ws/${symbol}`;
      const newWs = new WebSocket(wsUrl);

      newWs.onopen = () => {
        console.log('WebSocket Connected');
        setError(null);
      };

      newWs.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as CurrentPriceResponse;
          if (typeof data.price === 'number' && typeof data.timestamp === 'string') {
            setPrice(prev => {
              const dailyChange = openPrice ? 
                ((data.price - openPrice) / openPrice) * 100 : 
                0;

              return {
                price: data.price,
                timestamp: data.timestamp,
                openPrice: openPrice,
                dailyChange: dailyChange
              } as PriceData;
            });
          }
        } catch (e) {
          console.error('Error parsing WebSocket data:', e);
        }
      };

      newWs.onerror = () => {
        setError('WebSocket connection error');
      };

      newWs.onclose = () => {
        console.log('WebSocket disconnected, attempting to reconnect...');
        setTimeout(connectWebSocket, 3000);
      };

      setWs(newWs);
    };

    initialize();
    connectWebSocket();

    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [symbol]);

  // Loading state
  if (isConnecting && !price) {
    return (
      <div className="bg-white rounded-lg p-6 shadow-lg">
        <h2 className="text-xl font-semibold mb-4">{symbol} Price</h2>
        <div className="text-gray-500 flex items-center justify-center">
          <svg 
            className="animate-spin -ml-1 mr-3 h-5 w-5 text-gray-500" 
            xmlns="http://www.w3.org/2000/svg" 
            fill="none" 
            viewBox="0 0 24 24"
          >
            <circle 
              className="opacity-25" 
              cx="12" 
              cy="12" 
              r="10" 
              stroke="currentColor" 
              strokeWidth="4"
            ></circle>
            <path 
              className="opacity-75" 
              fill="currentColor" 
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            ></path>
          </svg>
          Connecting to market data...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg p-6 shadow-lg">
        <h2 className="text-xl font-semibold mb-4">{symbol} Price</h2>
        <div className="text-red-500">{error}</div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg p-6 shadow-lg">
      <h2 className="text-xl font-semibold mb-4">{symbol} Price</h2>
      {price ? (
        <div className="space-y-2">
          <div className="text-3xl font-bold text-blue-600">
            ${price.price.toLocaleString(undefined, {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}
          </div>
          {price.dailyChange !== null && (
            <div className={`text-sm font-medium ${getPriceChangeClass(price.dailyChange)}`}>
              {formatPriceChange(price.dailyChange)}
              <span className="text-gray-500 ml-1">today</span>
            </div>
          )}
          {price.openPrice && (
            <div className="text-sm text-gray-500">
              Open: ${price.openPrice.toLocaleString(undefined, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}
            </div>
          )}
          <div className="text-sm text-gray-500">
            Last updated: {new Date(price.timestamp).toLocaleString()}
          </div>
        </div>
      ) : (
        <div className="text-gray-500">Unable to fetch price data</div>
      )}
    </div>
  );
}

export default PriceDisplay;