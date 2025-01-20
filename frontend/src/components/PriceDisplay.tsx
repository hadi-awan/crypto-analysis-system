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
  onSelect?: () => void;
  isSelected?: boolean;
}

function PriceDisplay({ 
  symbol = 'BTC-USDT', 
  onSelect, 
  isSelected = false 
}: PriceDisplayProps) {
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

  useEffect(() => {
    let ws: WebSocket;

    const connectWebSocket = () => {
      setIsConnecting(true);
      ws = new WebSocket(`ws://127.0.0.1:8000/api/v1/crypto/ws/${symbol}`);

      ws.onopen = () => {
        console.log('WebSocket Connected');
        setIsConnecting(false);
        setError(null);
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
          console.error('Error parsing data:', e);
        }
      };

      ws.onerror = (e) => {
        console.error('WebSocket error:', e);
        setError('WebSocket connection error');
        setIsConnecting(false);
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected, attempting to reconnect...');
        setTimeout(connectWebSocket, 3000);
      };
    };

    connectWebSocket();

    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [symbol]);

  return (
    <div 
      className={`
        bg-white rounded-lg p-6 shadow-lg cursor-pointer
        transition-all duration-300 ease-in-out
        ${isSelected 
          ? 'ring-4 ring-blue-500 ring-opacity-50 transform scale-105' 
          : 'hover:bg-gray-50 hover:shadow-xl'}
      `}
      onClick={onSelect}
    >
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
        <div className="text-gray-500">Waiting for price updates...</div>
      )}
    </div>
  );
}

export default PriceDisplay;