import { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

interface MarketData {
  symbol: string;
  price: number;
  change_24h: number;
  volume_24h: number;
  market_cap: number;
  last_updated: string;
}

type SortKey = keyof Pick<MarketData, 'price' | 'change_24h' | 'volume_24h' | 'market_cap'>;
type SortDirection = 'asc' | 'desc';

function MarketOverview() {
  const [marketData, setMarketData] = useState<MarketData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Sorting state
  const [sortKey, setSortKey] = useState<SortKey>('market_cap');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  
  // Filtering state
  const [searchTerm, setSearchTerm] = useState('');

  const navigate = useNavigate();

  useEffect(() => {
    const fetchMarketData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const response = await axios.get('http://localhost:8000/api/v1/crypto/market', {
          params: {
            limit: 100,  // Fetch top 100 cryptocurrencies
            sort_by: 'market_cap'
          },
          timeout: 30000
        });
        
        console.log('Market data response:', response.data);
        
        // Validate response data
        if (!Array.isArray(response.data)) {
          throw new Error('Invalid response format');
        }
        
        setMarketData(response.data);
      } catch (err) {
        console.error('Error fetching market data:', err);
        
        // More detailed error handling
        if (axios.isAxiosError(err)) {
          if (err.response) {
            // The request was made and the server responded with a status code
            setError(`Server Error: ${err.response.data.detail || 'Unknown error'}`);
          } else if (err.request) {
            // The request was made but no response was received
            setError('No response received from server. Please check your connection.');
          } else {
            // Something happened in setting up the request
            setError('Error setting up the request');
          }
        } else {
          setError('An unexpected error occurred');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchMarketData();
    const interval = setInterval(fetchMarketData, 300000); // Update every 5 minutes

    return () => clearInterval(interval);
  }, []);

  // Format functions
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      notation: 'compact'
    }).format(value);
  };

  const formatPercentage = (value: number) => {
    return `${value > 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  // Sorting handler
  const handleSort = (key: SortKey) => {
    // If clicking the same column, toggle direction
    if (sortKey === key) {
      setSortDirection(sortDirection === 'desc' ? 'asc' : 'desc');
    } else {
      // New column, default to descending
      setSortKey(key);
      setSortDirection('desc');
    }
  };

  // Filtered and sorted data
  const processedMarketData = useMemo(() => {
    let result = marketData;

    // Filter by search term
    if (searchTerm) {
      const searchTermLower = searchTerm.toLowerCase();
      result = result.filter(asset => 
        asset.symbol.toLowerCase().includes(searchTermLower)
      );
    }

    // Sort the data
    return result.sort((a, b) => {
      const modifier = sortDirection === 'desc' ? -1 : 1;
      if (a[sortKey] < b[sortKey]) return -1 * modifier;
      if (a[sortKey] > b[sortKey]) return 1 * modifier;
      return 0;
    });
  }, [marketData, searchTerm, sortKey, sortDirection]);

  // Render loading state
  if (loading) {
    return (
      <div className="max-w-7xl mx-auto py-8 px-4">
        <div className="bg-white rounded-lg p-8 shadow-lg text-center">
          <div className="flex justify-center items-center">
            <svg 
              className="animate-spin -ml-1 mr-3 h-8 w-8 text-blue-500" 
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
            <span>Loading market data...</span>
          </div>
        </div>
      </div>
    );
  }

  // Render error state
  if (error) {
    return (
      <div className="max-w-7xl mx-auto py-8 px-4">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
          <strong className="font-bold">Error: </strong>
          <span className="block sm:inline">{error}</span>
        </div>
      </div>
    );
  }

  // Render empty state
  if (marketData.length === 0) {
    return (
      <div className="max-w-7xl mx-auto py-8 px-4">
        <div className="bg-white rounded-lg p-8 shadow-lg text-center">
          <p className="text-gray-500">No market data available</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto py-8 px-4">
      <div className="mb-6 flex justify-between items-center">
        <h1 className="text-2xl font-bold text-white">Market Overview</h1>
        <input 
          type="text"
          placeholder="Search cryptocurrencies"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div className="bg-white rounded-lg shadow-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Asset
                </th>
                <th 
                  className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('price')}
                >
                  Price 
                  {sortKey === 'price' && (
                    <span className="ml-1">
                      {sortDirection === 'desc' ? '▼' : '▲'}
                    </span>
                  )}
                </th>
                <th 
                  className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('change_24h')}
                >
                  24h Change
                  {sortKey === 'change_24h' && (
                    <span className="ml-1">
                      {sortDirection === 'desc' ? '▼' : '▲'}
                    </span>
                  )}
                </th>
                <th 
                  className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('volume_24h')}
                >
                  24h Volume
                  {sortKey === 'volume_24h' && (
                    <span className="ml-1">
                      {sortDirection === 'desc' ? '▼' : '▲'}
                    </span>
                  )}
                </th>
                <th 
                  className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('market_cap')}
                >
                  Market Cap
                  {sortKey === 'market_cap' && (
                    <span className="ml-1">
                      {sortDirection === 'desc' ? '▼' : '▲'}
                    </span>
                  )}
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {processedMarketData.map((asset) => (
                <tr 
                  key={asset.symbol}
                  className="hover:bg-gray-50 cursor-pointer"
                  onClick={() => navigate(`/analysis?pair=${asset.symbol.replace('/', '-')}`)}
                >
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="text-sm font-medium text-gray-900">
                        {asset.symbol}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                    {formatCurrency(asset.price)}
                  </td>
                  <td className={`px-6 py-4 whitespace-nowrap text-right text-sm ${
                    asset.change_24h > 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {formatPercentage(asset.change_24h)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                    {formatCurrency(asset.volume_24h)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                    {formatCurrency(asset.market_cap)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default MarketOverview;