import './App.css'

function App() {
  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto py-6 px-4">
          <h1 className="text-3xl font-bold text-gray-900">
            Crypto Analysis System
          </h1>
        </div>
      </header>
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="bg-white shadow-sm rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">BTC/USDT Price</h2>
          {/* We'll add price display here */}
          <div className="text-3xl font-bold text-blue-600">
            $50,000.00
          </div>
        </div>
      </main>
    </div>
  )
}

export default App