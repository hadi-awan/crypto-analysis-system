import './App.css'
import PriceDisplay from './components/PriceDisplay'
import PriceChart from './components/PriceChart'

function App() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-800">
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto py-6 px-4">
          <div className="flex justify-between items-center">
            <h1 className="text-3xl font-bold text-white">
              Crypto Analysis System
            </h1>
            <div className="text-gray-400 text-sm">
              Live Market Data
            </div>
          </div>
        </div>
      </header>
      <main className="max-w-7xl mx-auto py-8 px-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <PriceDisplay symbol="BTC-USDT" />
          <PriceDisplay symbol="ETH-USDT" />
          <PriceDisplay symbol="BNB-USDT" />
        </div>
        <div className="grid grid-cols-1 gap-6">
          <PriceChart symbol="BTC-USDT" />
        </div>
      </main>
    </div>
  )
}

export default App