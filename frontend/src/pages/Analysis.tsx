import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import axios from 'axios';
import PriceChart from '../components/PriceChart';
import TechnicalIndicators from '../components/TechnicalIndicators';
import CorrelationAnalysis from '../components/CorrelationAnalysis';
import HistoricalPerformance from '../components/HistoricalPerformance';
import SupportResistanceLevels from '../components/SupportResistanceLevels';
import VolumeAnalysis from '../components/VolumeAnalysis';
import CryptoSearch from '../components/CryptoSearch';

function AnalysisPage() {
  // Extract pair from URL query parameters
  const location = useLocation();
  const queryParams = new URLSearchParams(location.search);
  const [selectedPair, setSelectedPair] = useState(
    queryParams.get('pair') || 'BTC-USDT'
  );
  
  // State for additional analysis data
  const [analysisData, setAnalysisData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch comprehensive analysis data
  useEffect(() => {
    const fetchAnalysisData = async () => {
      try {
        setLoading(true);
        
        const response = await axios.get(`http://localhost:8000/api/v1/crypto/comprehensive-analysis/${selectedPair}`);
        
        setAnalysisData(response.data);
        setLoading(false);
      } catch (err) {
        console.error('Error fetching analysis data:', err);
        setError('Failed to fetch analysis data');
        setLoading(false);
      }
    };

    fetchAnalysisData();
  }, [selectedPair]);

  // Crypto pair selector
  const handlePairChange = (pair: string) => {
    setSelectedPair(pair);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-800 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-blue-500"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-800 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
            {error}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-800 p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Crypto Search and Pair Selection */}
        <div className="mb-6">
          <CryptoSearch 
            onSelectPair={handlePairChange} 
            defaultPair={selectedPair}
            className="w-full max-w-xl mx-auto"
          />
        </div>

        {/* Price Chart and Technical Indicators */}
        <div className="grid md:grid-cols-2 gap-6">
          <PriceChart symbol={selectedPair} />
          <TechnicalIndicators symbol={selectedPair} />
        </div>

        {/* Detailed Analysis Sections */}
        <div className="grid md:grid-cols-2 gap-6">
          <HistoricalPerformance 
            symbol={selectedPair} 
            historicalData={analysisData?.historical_performance}
          />
          <VolumeAnalysis 
            symbol={selectedPair} 
            volumeData={analysisData?.volume_analysis}
          />
        </div>

        {/* Advanced Analysis Sections */}
        <div className="grid md:grid-cols-2 gap-6">
          <CorrelationAnalysis 
            symbol={selectedPair} 
            correlationData={analysisData?.correlations}
          />
          <SupportResistanceLevels 
            symbol={selectedPair} 
            supportResistanceData={analysisData?.support_resistance}
          />
        </div>
      </div>
    </div>
  );
}

export default AnalysisPage;