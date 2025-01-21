import { useState } from 'react';
import PriceDisplay from '../components/PriceDisplay';
import PriceChart from '../components/PriceChart';
import TechnicalIndicators from '../components/TechnicalIndicators';
import CryptoSearch from '../components/CryptoSearch';

function Dashboard() {
  const [selectedPair, setSelectedPair] = useState('BTC-USDT');

  return (
    <div className="max-w-7xl mx-auto py-8 px-4 space-y-6">
      {/* Header with title and search */}
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-white">Dashboard</h1>
        <CryptoSearch 
          onSelectPair={setSelectedPair}
          className="w-96" // Adjust width as needed
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <PriceDisplay symbol={selectedPair} />
        <PriceDisplay symbol="ETH-USDT" />
        <PriceDisplay symbol="BNB-USDT" />
      </div>
      <PriceChart symbol={selectedPair} />
      <TechnicalIndicators symbol={selectedPair} />
    </div>
  );
}

export default Dashboard;