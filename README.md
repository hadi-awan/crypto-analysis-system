# Crypto Analysis System
A real-time cryptocurrency analysis platform built with FastAPI and React that provides live market data, technical analysis, and trading insights.

## Key Features
<li>Real-time price tracking for multiple cryptocurrencies</li>
<li>Interactive price charts with multiple timeframes (1H, 4H, 1D)</li>
<li>Technical indicators including RSI, MACD, and Bollinger Bands</li>
<li>WebSocket integration for live data updates</li>
<li>Responsive and modern UI built with TailwindCSS</li>

## Tech Stack
### Backend
<li>FastAPI for high-performance API endpoints</li>
<li>Python for data processing and technical analysis</li>
<li>WebSocket support for real-time data streaming</li>
<li>Pandas for data manipulation</li>

### Frontend
<li>React with TypeScript for type-safe development</li>
<li>TailwindCSS for styling</li>
<li>Recharts for interactive data visualization</li>
<li>Axios for API communication</li>
<li>WebSocket client for real-time updates</li>

## Architecture
### Backend (Python/FastAPI)
<li><b>Data Collection:</b> Real-time price data collection using CCXT library for unified crypto exchange access</li>
<li><b>Technical Analysis:</b> Custom implementation of technical indicators: 
  <ul>RSI (Relative Strength Index)</ul>
  <ul>MACD (Moving Average Convergence Divergence)</ul>
  <ul>Bollinger Bands</ul>
</li>
<li><b>Real-time Updates:</b> WebSocket implementation for live price and indicator updates</li>
<li><b>Data Processing:</b> Pandas for efficient time-series data manipulation</li>
<li><b>Error Handling</b> Comprehensive validation and error handling for API responses</li>

### Frontend (React/TypeScript)
<li><b>State Management:</b> React hooks for local state management</li>
<li><b>Data Visualization:</b> Recharts for responsive and interactive charts</li>
<li><b>Real-time Updates:</b> WebSocket client for live data streaming</li>
<li><b>Type Safety:</b> TypeScript for enhanced development experience and error prevention</li>
<li><b>Styling:</b> TailwindCSS for utility-first styling and responsive design</li>

## Setup Instructions
### Backend Setup
```
# Clone the repository
git clone https://github.com/yourusername/crypto-analysis-system.git
cd crypto-analysis-system

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
cd backend
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configurations

# Run the server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend Setup
```
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Environment Variables
```
# Backend (.env)
API_V1_STR=/api/v1
PROJECT_NAME=Crypto Analysis System
BACKEND_CORS_ORIGINS=["http://localhost:5173"]
DATABASE_URL=your_database_url
BINANCE_API_KEY=your_api_key
BINANCE_SECRET_KEY=your_secret_key

# Additional configurations for JWT and other services
```

### API Endpoints
<li>GET /api/v1/crypto/price/{pair}: Get current price for a trading pair</li>
<li>GET /api/v1/crypto/historical/{pair}: Get historical price data with timeframe options</li>
<li>GET /api/v1/crypto/indicators/{pair}: Get technical indicators</li>
<li>WebSocket /api/v1/crypto/ws/{pair}: Real-time price updates</li>

### Features
<li>Live price tracking for multiple cryptocurrency pairs</li>
<li>Interactive price charts with multiple timeframes (1H, 4H, 1D)</li>
<li>Real-time technical indicators</li>
<li>Performance optimization for handling large datasets</li>
<li>Responsive design for desktop and mobile views</li>
<li>Error handling and data validation</li>
<li>WebSocket integration for real-time updates</li>

### Future Enhancements
<li>User authentication and portfolio tracking</li>
<li>Additional technical indicators</li>
<li>Trading signals based on indicator combinations</li>
<li>Historical performance analysis</li>
<li>Price alerts and notifications</li>


