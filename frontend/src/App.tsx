import { useState } from 'react';
import './App.css'
import PriceDisplay from './components/PriceDisplay'
import PriceChart from './components/PriceChart'
import TechnicalIndicators from './components/TechnicalIndicators'
import CryptoSearch from './components/CryptoSearch'

function App() {
  const [selectedPair, setSelectedPair] = useState('BTC-USDT');
  const [additionalPairs, setAdditionalPairs] = useState<string[]>(['ETH-USDT', 'BNB-USDT']);

  const handlePairSelect = (pair: string) => {
    // If the pair is not already in additional pairs, add it
    if (!additionalPairs.includes(pair) && pair !== selectedPair) {
      // If we have more than 3 pairs, remove the oldest one
      const updatedPairs = additionalPairs.length >= 3 
        ? [...additionalPairs.slice(1), pair]
        : [...additionalPairs, pair];
      
      setAdditionalPairs(updatedPairs);
    }
    
    // Set the selected pair to the newly selected pair
    setSelectedPair(pair);
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-800">
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto py-6 px-4">
          <div className="flex justify-between items-center">
            <h1 className="text-3xl font-bold text-white">
              Crypto Analysis System
            </h1>
            <div className="text-gray-400 text-sm">
              <CryptoSearch 
                onSelectPair={handlePairSelect} 
                className="w-80"
              />
            </div>
          </div>
        </div>
      </header>
      <main className="max-w-7xl mx-auto py-8 px-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          {additionalPairs.map(pair => (
            <PriceDisplay 
              key={pair} 
              symbol={pair} 
              onSelect={() => setSelectedPair(pair)}
              isSelected={pair === selectedPair}
            />
          ))}
        </div>
        <div className="grid grid-cols-1 gap-6">
          <PriceChart symbol={selectedPair} />
          <TechnicalIndicators symbol={selectedPair} />
        </div>
      </main>
    </div>
  )
}

export default App