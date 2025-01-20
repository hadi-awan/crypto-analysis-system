import React, { useState, useEffect } from 'react';

interface IndicatorData {
  rsi: number;
  macd: {
    macd: number;
    signal: number;
    histogram: number;
  };
  bb: {
    upper: number;
    middle: number;
    lower: number;
  };
  signals: Array<{
    type: 'BUY' | 'SELL' | 'NEUTRAL';
    indicator: string;
    strength: number;
    message: string;
  }>;
}

interface TechnicalIndicatorsProps {
  symbol: string;
}

function TechnicalIndicators({ symbol }: TechnicalIndicatorsProps) {
  const [data, setData] = useState<IndicatorData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [ws, setWs] = useState<WebSocket | null>(null);

  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        const response = await fetch(
          `http://localhost:8000/api/v1/crypto/indicators/${symbol}?indicators=rsi,macd,bb&timeframe=1h`
        );
        const initialData = await response.json();
        setData(initialData);
        setLoading(false);
      } catch (error) {
        setError('Failed to fetch initial indicator data');
        setLoading(false);
      }
    };

    const connectWebSocket = () => {
      const wsUrl = `ws://127.0.0.1:8000/api/v1/crypto/ws/${symbol}`;
      const newWs = new WebSocket(wsUrl);

      newWs.onopen = () => {
        console.log('WebSocket connected for indicators');
        setError(null);
      };

      newWs.onmessage = async (event) => {
        try {
          const response = await fetch(
            `http://localhost:8000/api/v1/crypto/indicators/${symbol}?indicators=rsi,macd,bb&timeframe=1h`
          );
          const newData = await response.json();
          setData(newData);
        } catch (error) {
          console.error('Error updating indicators:', error);
        }
      };

      newWs.onerror = () => {
        setError('WebSocket connection error');
      };

      newWs.onclose = () => {
        console.log('WebSocket closed, attempting to reconnect...');
        setTimeout(connectWebSocket, 3000);
      };

      setWs(newWs);
    };

    fetchInitialData();
    connectWebSocket();

    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [symbol]);

  const getSignalBadge = (signal: IndicatorData['signals'][0]) => {
    const baseClasses = "px-2 py-1 rounded-full text-xs font-medium";
    const colorClasses = signal.type === 'BUY' 
      ? 'bg-green-100 text-green-800'
      : 'bg-red-100 text-red-800';
    
    return (
      <div className={`${baseClasses} ${colorClasses} flex items-center gap-1`}>
        <span>{signal.type}</span>
        <span className="text-xs opacity-75">
          ({(signal.strength * 100).toFixed(0)}%)
        </span>
      </div>
    );
  };

  const getSignalForIndicator = (indicator: string) => {
    if (!data?.signals) return null;
    return data.signals.find(signal => signal.indicator === indicator);
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg p-4 shadow-lg">
        <div className="text-gray-500">Loading indicators...</div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="bg-white rounded-lg p-4 shadow-lg">
        <div className="text-red-500">{error || 'No data available'}</div>
      </div>
    );
  }

  const getRSIColor = (value: number) => {
    if (value >= 70) return 'text-red-500';
    if (value <= 30) return 'text-green-500';
    return 'text-gray-700';
  };

  return (
    <div className="bg-white rounded-lg p-4 shadow-lg">
      <div className="flex items-baseline justify-between mb-4">
        <h2 className="text-lg font-semibold">Technical Indicators</h2>
        <span className="text-sm text-gray-500">{symbol}</span>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* RSI */}
        <div className="border rounded-lg p-4">
          <div className="flex justify-between items-start mb-2">
            <h3 className="text-sm font-medium text-gray-500">RSI (14)</h3>
            {getSignalForIndicator('RSI') && getSignalBadge(getSignalForIndicator('RSI')!)}
          </div>
          <div className={`text-2xl font-bold ${getRSIColor(data.rsi)}`}>
            {data.rsi.toFixed(2)}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            {data.rsi >= 70 ? 'Overbought' : data.rsi <= 30 ? 'Oversold' : 'Neutral'}
          </div>
        </div>

        {/* MACD */}
        <div className="border rounded-lg p-4">
          <div className="flex justify-between items-start mb-2">
            <h3 className="text-sm font-medium text-gray-500">MACD</h3>
            {getSignalForIndicator('MACD') && getSignalBadge(getSignalForIndicator('MACD')!)}
          </div>
          <div className="space-y-1">
            <div className="flex justify-between">
              <span className="text-sm text-gray-500">MACD</span>
              <span className={`font-medium ${data.macd.macd > 0 ? 'text-green-500' : 'text-red-500'}`}>
                {data.macd.macd.toFixed(2)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-500">Signal</span>
              <span className="font-medium">{data.macd.signal.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-500">Histogram</span>
              <span className={`font-medium ${data.macd.histogram > 0 ? 'text-green-500' : 'text-red-500'}`}>
                {data.macd.histogram.toFixed(2)}
              </span>
            </div>
          </div>
        </div>

        {/* Bollinger Bands */}
        <div className="border rounded-lg p-4">
          <div className="flex justify-between items-start mb-2">
            <h3 className="text-sm font-medium text-gray-500">Bollinger Bands</h3>
            {getSignalForIndicator('BB') && getSignalBadge(getSignalForIndicator('BB')!)}
          </div>
          <div className="space-y-1">
            <div className="flex justify-between">
              <span className="text-sm text-gray-500">Upper</span>
              <span className="font-medium">${data.bb.upper.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-500">Middle</span>
              <span className="font-medium">${data.bb.middle.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-500">Lower</span>
              <span className="font-medium">${data.bb.lower.toLocaleString()}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default TechnicalIndicators;