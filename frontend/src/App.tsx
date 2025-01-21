import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/NavBar';
import Dashboard from './pages/Dashboard';
import MarketOverview from './pages/MarketOverview';
import Analysis from './pages/Analysis';
import About from './pages/About';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-800">
        <Navbar />
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/market" element={<MarketOverview />} />
          <Route path="/analysis" element={<Analysis />} />
          <Route path="/about" element={<About />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;