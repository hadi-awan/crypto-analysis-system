import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useState, useEffect } from 'react';
import axios from 'axios';

interface ChartData {
  timestamp: string;
  close: number;
}

interface ApiResponse {
  pair: string;
  timeframe: string;
  data: {
    timestamp: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
  }[];
}

interface PriceChartProps {
  symbol: string;
  timeframe?: string;
}

function PriceChart({ symbol, timeframe = '1m' }: PriceChartProps) {
  const [data, setData] = useState<ChartData[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        console.log(`Fetching chart data for ${symbol} with timeframe ${timeframe}`);
        const currentTime = new Date();
        console.log('Current time:', currentTime.toLocaleTimeString());

        const response = await axios.get<ApiResponse>(
          `http://localhost:8000/api/v1/crypto/historical/${symbol}`,
          { 
            params: { 
              symbol, 
              timeframe,
              _t: new Date().getTime()
            },
            timeout: 10000
          }
        );
        
        const formattedData = response.data.data.map(item => ({
          timestamp: new Date(item.timestamp).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
            hour12: true,
            timeZone: 'America/Toronto'
          }),
          close: item.close
        }));

        setData(formattedData);
      } catch (err) {
        // ... error handling ...
      } finally {
        setLoading(false);
      }
    };

    // Initial fetch
    fetchData();

    // Set up polling every 10 seconds
    const interval = setInterval(fetchData, 10000);

    // Cleanup
    return () => clearInterval(interval);
  }, [symbol, timeframe]);

  // Loading state
  if (loading) {
    return (
      <div className="h-[400px] bg-white rounded-lg p-4 shadow-lg flex items-center justify-center">
        <div className="text-gray-500">Loading chart data...</div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="h-[400px] bg-white rounded-lg p-4 shadow-lg flex items-center justify-center">
        <div className="flex flex-col items-center">
          <div className="text-red-500 text-lg mb-2">Chart Data Error</div>
          <div className="text-gray-600 text-sm text-center mb-4">{error}</div>
          <div className="text-xs text-gray-500 text-center">
            Possible issues:
            - Verify backend server is running
            - Check network connectivity
            - Confirm API endpoint exists
          </div>
        </div>
      </div>
    );
  }

  // No data state
  if (data.length === 0) {
    return (
      <div className="h-[400px] bg-white rounded-lg p-4 shadow-lg flex items-center justify-center">
        <div className="text-yellow-600">No chart data available</div>
      </div>
    );
  }

  // Chart rendering
  return (
    <div className="h-[400px] bg-white rounded-lg p-4 shadow-lg">
      <h3 className="text-lg font-semibold mb-4">{symbol} Price Chart</h3>
      <ResponsiveContainer width="100%" height="90%">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="timestamp"
            tick={{ fontSize: 12 }}
          />
          <YAxis 
            domain={['auto', 'auto']}
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
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export default PriceChart;