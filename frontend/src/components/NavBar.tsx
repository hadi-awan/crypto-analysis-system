import { Link } from 'react-router-dom';

function Navbar() {
  return (
    <nav className="bg-gray-800">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center">
            <Link to="/" className="text-white font-bold text-xl">
              Crypto Analysis System
            </Link>
          </div>
          <div className="flex space-x-4">
            <Link to="/" className="text-gray-300 hover:text-white px-3 py-2">
              Dashboard
            </Link>
            <Link to="/market" className="text-gray-300 hover:text-white px-3 py-2">
              Market Overview
            </Link>
            <Link to="/analysis" className="text-gray-300 hover:text-white px-3 py-2">
              Analysis
            </Link>
            <Link to="/about" className="text-gray-300 hover:text-white px-3 py-2">
              About
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;