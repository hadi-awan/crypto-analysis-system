
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface ChartData {
  timestamp: string;
  close: number;
}

interface PriceChartProps {
  symbol: string;
  initialTimeframe?: '1h' | '4h' | '1d';
}

interface TimeframeOption {
  label: string;
  value: '1h' | '4h' | '1d';
}

const timeframeOptions: TimeframeOption[] = [
  { label: '1 Hour', value: '1h' },
  { label: '4 Hours', value: '4h' },
  { label: '1 Day', value: '1d' }
];

function PriceChart({ symbol, initialTimeframe = '1h' }: PriceChartProps) {
  const [data, setData] = useState<ChartData[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeframe, setTimeframe] = useState<TimeframeOption['value']>(initialTimeframe);
  const [ws, setWs] = useState<WebSocket | null>(null);

  // Calculate y-axis domain based on current data
  const yAxisDomain = useMemo(() => {
    if (data.length === 0) return ['auto', 'auto'];

    const prices = data.map(d => d.close);
    const min = Math.min(...prices);
    const max = Math.max(...prices);
    const padding = (max - min) * 0.1; // Add 10% padding

    return [
      Math.max(0, min - padding), // Ensure we don't go below 0
      max + padding
    ];
  }, [data]);

  // Function to fetch initial historical data
  const fetchInitialData = useCallback(async () => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/crypto/historical/${symbol}?timeframe=${timeframe}`
      );
      const data = await response.json();
      
      const formattedData = data.data.map((item: any) => ({
        timestamp: new Date(item.timestamp).toLocaleTimeString([], {
          hour: '2-digit',
          minute: '2-digit',
          hour12: true,
          timeZone: 'America/Toronto'
        }),
        close: item.close
      }));

      setData(formattedData);
      setLoading(false);
    } catch (error) {
      setError('Failed to fetch initial chart data');
      setLoading(false);
    }
  }, [symbol, timeframe]);

  // WebSocket connection management
  useEffect(() => {
    const connectWebSocket = () => {
      const wsUrl = `ws://127.0.0.1:8000/api/v1/crypto/ws/${symbol}`;
      const newWs = new WebSocket(wsUrl);

      newWs.onopen = () => {
        console.log('WebSocket connected for chart');
        setError(null);
      };

      newWs.onmessage = (event) => {
        const message = JSON.parse(event.data);
        setData(prevData => {
          // Create new data point
          const newPoint = {
            timestamp: new Date(message.timestamp).toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit',
              hour12: true,
              timeZone: 'America/Toronto'
            }),
            close: message.price
          };

          // Add new point and maintain timeframe window
          const newData = [...prevData, newPoint];
          const timeframeMinutes = {
            '1h': 60,
            '4h': 240,
            '1d': 1440
          }[timeframe];

          return newData.slice(-timeframeMinutes);
        });
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

    // Reset data when symbol changes
    setData([]);
    setLoading(true);

    // Fetch initial data and establish WebSocket connection
    fetchInitialData();
    connectWebSocket();

    // Cleanup
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [symbol, timeframe, fetchInitialData]);

  // Loading state
  if (loading && data.length === 0) {
    return (
      <div className="h-96 bg-white rounded-lg p-4 shadow-lg flex items-center justify-center">
        <div className="text-gray-500">Loading chart data...</div>
      </div>
    );
  }

  // Error state
  if (error && data.length === 0) {
    return (
      <div className="h-96 bg-white rounded-lg p-4 shadow-lg flex items-center justify-center">
        <div className="flex flex-col items-center">
          <div className="text-red-500 text-lg mb-2">Chart Data Error</div>
          <div className="text-gray-600 text-sm text-center mb-4">{error}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-96 bg-white rounded-lg p-4 shadow-lg">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">{symbol} Price Chart</h3>
        <div className="flex gap-2">
          {timeframeOptions.map(option => (
            <button
              key={option.value}
              onClick={() => setTimeframe(option.value)}
              className={`px-3 py-1 rounded-md text-sm ${
                timeframe === option.value
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>
      <ResponsiveContainer width="100%" height="90%">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="timestamp"
            tick={{ fontSize: 12 }}
          />
          <YAxis 
            domain={yAxisDomain}
            tick={{ fontSize: 12 }}
            width={80}
            tickFormatter={(value) => `$${value.toLocaleString()}`}
          />
          <Tooltip 
            formatter={(value: number) => [`$${value.toLocaleString()}`, 'Price']}
          />
          <Line 
            type="monotone" 
            dataKey="close" 
            stroke="#2563eb" 
            dot={false}
            strokeWidth={2}
            isAnimationActive={false} // Disable animation for smoother updates
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export default PriceChart;
