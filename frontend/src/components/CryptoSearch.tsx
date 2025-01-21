import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';

interface CryptoPair {
  symbol: string;
  base: string;
  quote: string;
  category: string;
  keywords?: string[];
}

interface CryptoPairsResponse {
  total_pairs: number;
  pairs: CryptoPair[];
  error?: string;
}

interface CryptoSearchProps {
  onSelectPair: (pair: string) => void;
  className?: string;
  defaultPair?: string; // Added optional default pair
}

function CryptoSearch({ 
  onSelectPair, 
  className, 
  defaultPair = 'BTC-USDT' 
}: CryptoSearchProps) {
  const [searchTerm, setSearchTerm] = useState(defaultPair);
  const [pairs, setPairs] = useState<CryptoPair[]>([]);
  const [filteredPairs, setFilteredPairs] = useState<CryptoPair[]>([]);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const searchRef = useRef<HTMLDivElement>(null);

  // Fetch available pairs
  useEffect(() => {
    const fetchPairs = async () => {
      // Skip if search term is too short
      if (searchTerm.length < 1) {
        setFilteredPairs([]);
        return;
      }

      setLoading(true);
      setError(null);
      try {
        const response = await axios.get(
          'http://localhost:8000/api/v1/crypto/pairs', 
          {
            params: {
              search: searchTerm,
              quote_currencies: ['USDT', 'BTC', 'ETH', 'BNB']
            }
          }
        );
        
        // Type assertion to handle unknown type
        const responseData = response.data as CryptoPairsResponse;
        
        // Type-safe data extraction
        const fetchedPairs = responseData.pairs || [];
        setPairs(fetchedPairs);
        setFilteredPairs(fetchedPairs.slice(0, 50)); // Limit initial results

        // Check for any errors in the response
        if (responseData.error) {
          setError(responseData.error);
        }

        // Open dropdown if there are results
        setIsDropdownOpen(fetchedPairs.length > 0);
      } catch (error: unknown) {
        console.error('Error fetching crypto pairs:', error);
        
        if (error instanceof Error) {
          setError(error.message);
        } else {
          setError('An unexpected error occurred');
        }
      } finally {
        setLoading(false);
      }
    };

    // Debounce search to reduce unnecessary API calls
    const timeoutId = setTimeout(fetchPairs, 300);
    return () => clearTimeout(timeoutId);
  }, [searchTerm]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleSelectPair = (pair: CryptoPair) => {
    onSelectPair(pair.symbol.replace('/', '-'));
    setSearchTerm(pair.symbol);
    setIsDropdownOpen(false);
  };

  return (
    <div 
      ref={searchRef} 
      className={`relative w-full max-w-md ${className}`}
    >
      <input 
        type="text"
        placeholder="Search cryptocurrencies (BTC, ETH, XRP, etc.)"
        value={searchTerm}
        onChange={(e) => {
          setSearchTerm(e.target.value);
          // Only show dropdown if there's a search term
          setIsDropdownOpen(e.target.value.length > 0);
        }}
        onFocus={() => {
          // Show dropdown if there are filtered pairs
          setIsDropdownOpen(filteredPairs.length > 0);
        }}
        className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      
      {isDropdownOpen && (
        <div className="absolute z-10 mt-1 w-full max-h-60 overflow-y-auto bg-white border rounded-md shadow-lg">
          {loading && (
            <div className="p-4 text-center text-gray-500">
              Searching pairs...
            </div>
          )}
          
          {error && (
            <div className="p-4 text-center text-red-500">
              {error}
            </div>
          )}
          
          {!loading && !error && filteredPairs.length === 0 && (
            <div className="p-4 text-center text-gray-500">
              No matching pairs found. Try a different search term.
            </div>
          )}
          
          {filteredPairs.map((pair) => (
            <div 
              key={pair.symbol}
              onClick={() => handleSelectPair(pair)}
              className="px-4 py-2 hover:bg-gray-100 cursor-pointer flex justify-between items-center border-b last:border-b-0"
            >
              <div className="flex flex-col">
                <span className="font-bold">{pair.symbol}</span>
                <span className="text-xs text-gray-500">
                  {pair.base} / {pair.quote}
                </span>
              </div>
              <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                {pair.category}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default CryptoSearch;