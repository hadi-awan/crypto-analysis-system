import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

interface HistoricalPerformanceProps {
  symbol: string;
  historicalData?: {
    yearly_returns: Array<{year: number, return_percentage: number}>;
    total_return: number;
    volatility: number;
    max_drawdown: number;
  };
}

function HistoricalPerformance({ symbol, historicalData }: HistoricalPerformanceProps) {
  if (!historicalData) {
    return (
      <div className="bg-white rounded-lg p-4 shadow-lg">
        <h2 className="text-lg font-semibold mb-4">Historical Performance</h2>
        <p className="text-gray-500">No historical data available</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg p-4 shadow-lg">
      <h2 className="text-lg font-semibold mb-4">Historical Performance - {symbol}</h2>
      
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="bg-gray-100 p-3 rounded">
          <h3 className="text-sm text-gray-600">Total Return</h3>
          <p className={`text-lg font-bold ${historicalData.total_return >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {historicalData.total_return.toFixed(2)}%
          </p>
        </div>
        <div className="bg-gray-100 p-3 rounded">
          <h3 className="text-sm text-gray-600">Volatility</h3>
          <p className="text-lg font-bold text-blue-600">
            {historicalData.volatility.toFixed(2)}%
          </p>
        </div>
      </div>

      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={historicalData.yearly_returns}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="year" />
            <YAxis 
              label={{ 
                value: 'Return (%)', 
                angle: -90, 
                position: 'insideLeft' 
              }}
            />
            <Tooltip 
              formatter={(value) => [`${value}%`, 'Return']}
              contentStyle={{ backgroundColor: '#f3f4f6' }}
            />
            <Bar 
              dataKey="return_percentage" 
              fill="#3B82F6"
              maxBarSize={50}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-4 text-sm text-gray-600">
        <p>Max Drawdown: {historicalData.max_drawdown.toFixed(2)}%</p>
      </div>
    </div>
  );
}

export default HistoricalPerformance;