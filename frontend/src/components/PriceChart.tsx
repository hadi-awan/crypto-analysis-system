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

function PriceChart({ symbol, timeframe = '1h' }: PriceChartProps) {
  const [data, setData] = useState<ChartData[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Log the exact request details for debugging
        console.log(`Fetching chart data for ${symbol} with timeframe ${timeframe}`);

        const response = await axios.get<ApiResponse>(
          `http://localhost:8000/api/v1/crypto/historical/${symbol}`,
          { 
            params: { timeframe },
            timeout: 10000 // 10-second timeout
          }
        );
        
        // Comprehensive response logging
        console.log('Full API Response:', {
          status: response.status,
          data: response.data
        });
        
        // Validate response data
        if (!response.data || !response.data.data || response.data.data.length === 0) {
          throw new Error('No chart data received');
        }
        
        // Format data for chart
        const formattedData = response.data.data.map(item => ({
          timestamp: new Date(item.timestamp).toLocaleTimeString(),
          close: item.close
        })).reverse(); // Reverse to show most recent data first

        console.log('Formatted Chart Data:', formattedData);
        setData(formattedData);
      } catch (err: unknown) {
        // Comprehensive error handling
        if (
          err !== null && 
          typeof err === 'object' && 
          'response' in err &&
          'request' in err
        ) {
          const error = err as { 
            response?: { status: number, data: any }, 
            request?: any, 
            message?: string 
          };

          if (error.response) {
            // The request was made and the server responded with a status code
            // that falls out of the range of 2xx
            console.error('Server responded with error:', {
              status: error.response.status,
              data: error.response.data
            });

            switch (error.response.status) {
              case 404:
                setError('Endpoint not found. Check your API configuration.');
                break;
              case 500:
                setError('Server error. Please try again later.');
                break;
              default:
                setError(`API Error: ${error.response.status}`);
            }
          } else if (error.request) {
            // The request was made but no response was received
            console.error('No response received:', error.request);
            setError('No response from server. Check your network connection.');
          } else {
            // Something happened in setting up the request that triggered an Error
            console.error('Error setting up request:', error.message);
            setError('Error setting up the request. Please check your configuration.');
          }
        } else {
          // Handle non-axios errors
          console.error('Unexpected error:', err);
          setError(err instanceof Error ? err.message : 'An unknown error occurred');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchData();
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