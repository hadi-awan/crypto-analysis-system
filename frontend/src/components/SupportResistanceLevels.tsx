import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface SupportResistanceLevelsProps {
  symbol: string;
  supportResistanceData?: {
    price_history: Array<{date: string, price: number}>;
    support_levels: Array<{level: number, strength: number}>;
    resistance_levels: Array<{level: number, strength: number}>;
    current_price: number;
  };
}

function SupportResistanceLevels({ symbol, supportResistanceData }: SupportResistanceLevelsProps) {
  if (!supportResistanceData) {
    return (
      <div className="bg-white rounded-lg p-4 shadow-lg">
        <h2 className="text-lg font-semibold mb-4">Support & Resistance Levels</h2>
        <p className="text-gray-500">No support/resistance data available</p>
      </div>
    );
  }

  // Prepare chart data with support and resistance levels
  const chartData = supportResistanceData.price_history.map(point => ({
    ...point,
    support: supportResistanceData.support_levels.find(s => 
      Math.abs(s.level - point.price) < point.price * 0.01
    )?.level,
    resistance: supportResistanceData.resistance_levels.find(r => 
      Math.abs(r.level - point.price) < point.price * 0.01
    )?.level
  }));

  return (
    <div className="bg-white rounded-lg p-4 shadow-lg">
      <h2 className="text-lg font-semibold mb-4">Support & Resistance Levels - {symbol}</h2>
      
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="bg-gray-100 p-3 rounded">
          <h3 className="text-sm text-gray-600">Current Price</h3>
          <p className="text-lg font-bold text-blue-600">
            ${supportResistanceData.current_price.toLocaleString()}
          </p>
        </div>
        <div className="bg-gray-100 p-3 rounded">
          <h3 className="text-sm text-gray-600">Key Support/Resistance</h3>
          <div className="flex justify-between">
            <div>
              <span className="text-sm text-gray-500">Support</span>
              <p className="text-green-600 font-medium">
                ${supportResistanceData.support_levels[0]?.level.toLocaleString() || 'N/A'}
              </p>
            </div>
            <div>
              <span className="text-sm text-gray-500">Resistance</span>
              <p className="text-red-600 font-medium">
                ${supportResistanceData.resistance_levels[0]?.level.toLocaleString() || 'N/A'}
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis 
              label={{ 
                value: 'Price', 
                angle: -90, 
                position: 'insideLeft' 
              }}
            />
            <Tooltip 
              formatter={(value, name) => {
                if (name === 'price') {
                  return [`$${Number(value).toLocaleString()}`, 'Price'];
                }
                return [value, name];
              }}
            />
            <Line 
              type="monotone" 
              dataKey="price" 
              stroke="#3B82F6" 
              dot={false}
            />
            {/* Support and Resistance Level Lines */}
            <Line 
              type="monotone" 
              dataKey="support" 
              stroke="#10B981"  // Green for support
              strokeDasharray="5 5"
              dot={false}
            />
            <Line 
              type="monotone" 
              dataKey="resistance" 
              stroke="#EF4444"  // Red for resistance
              strokeDasharray="5 5"
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-4">
        <h3 className="text-sm font-semibold text-gray-600 mb-2">Support Levels</h3>
        <div className="flex space-x-2">
          {supportResistanceData.support_levels.slice(0, 3).map((level, index) => (
            <div 
              key={index} 
              className="bg-green-100 text-green-800 px-2 py-1 rounded text-xs"
            >
              ${level.level.toLocaleString()} (Strength: {level.strength.toFixed(2)})
            </div>
          ))}
        </div>

        <h3 className="text-sm font-semibold text-gray-600 mt-2 mb-2">Resistance Levels</h3>
        <div className="flex space-x-2">
          {supportResistanceData.resistance_levels.slice(0, 3).map((level, index) => (
            <div 
              key={index} 
              className="bg-red-100 text-red-800 px-2 py-1 rounded text-xs"
            >
              ${level.level.toLocaleString()} (Strength: {level.strength.toFixed(2)})
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default SupportResistanceLevels;