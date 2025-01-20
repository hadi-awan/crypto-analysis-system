import { useEffect, useState } from 'react';
import axios from 'axios';

interface PriceData {
  price: number;
  timestamp: string;
  lastSignificantPrice?: number;
  lastSignificantTime?: string;
  changePercent?: number;
}

interface PriceDisplayProps {
  symbol?: string;
}

function PriceDisplay({ symbol = 'BTC-USDT' }: PriceDisplayProps) {
  const [price, setPrice] = useState<PriceData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isConnecting, setIsConnecting] = useState(true);

  const SIGNIFICANT_UPDATE_INTERVAL = 60000; // 1 minute in milliseconds

  const getPriceChangeClass = (change: number) => {
    if (change === 0) return 'text-gray-500';
    return change > 0 ? 'text-green-500' : 'text-red-500';
  };

  const formatPriceChange = (change: number) => {
    const sign = change > 0 ? '+' : '';
    return `${sign}${change.toFixed(2)}%`;
  };

  // Fetch initial price before WebSocket connection
  useEffect(() => {
    const fetchInitialPrice = async () => {
      try {
        const response = await axios.get(`http://localhost:8000/api/v1/crypto/price/${symbol}`);
        const initialPriceData = {
          price: response.data.price,
          timestamp: response.data.timestamp,
          changePercent: 0
        };
        setPrice(initialPriceData);
        setIsConnecting(false);
      } catch (error) {
        console.error('Error fetching initial price:', error);
        setError('Failed to fetch initial price');
        setIsConnecting(false);
      }
    };

    fetchInitialPrice();
  }, [symbol]);

  useEffect(() => {
    let ws: WebSocket;
    let reconnectTimeout: NodeJS.Timeout;

    const connectWebSocket = () => {
      setIsConnecting(true);
      setError(null);

      ws = new WebSocket(`ws://127.0.0.1:8000/api/v1/crypto/ws/${symbol}`);

      ws.onopen = () => {
        console.log('WebSocket Connected');
        setIsConnecting(false);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (typeof data.price === 'number' && typeof data.timestamp === 'string') {
            setPrice(prev => {
              const now = new Date().getTime();
              const lastSignificantTime = new Date(prev?.lastSignificantTime || 0).getTime();
              
              const shouldUpdateReference = 
                !prev || 
                (prev.price !== data.price && 
                (now - lastSignificantTime >= SIGNIFICANT_UPDATE_INTERVAL));

              const changePercent = prev?.lastSignificantPrice 
                ? ((data.price - prev.lastSignificantPrice) / prev.lastSignificantPrice) * 100 
                : 0;

              return {
                price: data.price,
                timestamp: data.timestamp,
                lastSignificantPrice: shouldUpdateReference ? data.price : prev?.lastSignificantPrice,
                lastSignificantTime: shouldUpdateReference ? data.timestamp : prev?.lastSignificantTime,
                changePercent: shouldUpdateReference ? 0 : changePercent
              };
            });
          }
        } catch (e) {
          console.error('Error parsing WebSocket data:', e);
        }
      };

      ws.onerror = (e) => {
        console.error('WebSocket error:', e);
        setError('WebSocket connection error');
        setIsConnecting(false);
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected, attempting to reconnect...');
        setIsConnecting(true);
        reconnectTimeout = setTimeout(connectWebSocket, 3000);
      };
    };

    connectWebSocket();

    return () => {
      if (ws) {
        ws.close();
      }
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
      }
    };
  }, [symbol]);

  // Loading or error state
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
          {price.changePercent !== undefined && (
            <div className={`text-sm font-medium ${getPriceChangeClass(price.changePercent)}`}>
              {formatPriceChange(price.changePercent)}
              <span className="text-gray-500 ml-1">in the last minute</span>
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