import { useState } from 'react';
import PriceDisplay from '../components/PriceDisplay';
import PriceChart from '../components/PriceChart';
import TechnicalIndicators from '../components/TechnicalIndicators';
import CryptoSearch from '../components/CryptoSearch';

function Dashboard() {
  const [selectedPair, setSelectedPair] = useState('BTC-USDT'); // Default pair

  return (
    <div className="max-w-7xl mx-auto py-8 px-4 space-y-6">
      {/* CryptoSearch allows the user to select a trading pair */}
      <div className="flex justify-center mb-6">
        <CryptoSearch 
          onSelectPair={(pair) => setSelectedPair(pair)} // Dynamically update the selected pair
          className="w-full max-w-xl"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Displays the selected pair dynamically */}
        <PriceDisplay symbol={selectedPair} />
        <PriceDisplay symbol="ETH-USDT" />
        <PriceDisplay symbol="BNB-USDT" />
      </div>
      <PriceChart symbol={selectedPair} /> {/* Chart for the selected pair */}
      <TechnicalIndicators symbol={selectedPair} /> {/* Technical indicators for the selected pair */}
    </div>
  );
}

export default Dashboard;
