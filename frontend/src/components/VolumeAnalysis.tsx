import React from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

interface VolumeAnalysisProps {
  symbol: string;
  volumeData?: {
    daily_volume: Array<{date: string, volume: number}>;
    avg_daily_volume: number;
    volume_trend: 'increasing' | 'decreasing' | 'neutral';
    max_volume_day: {date: string, volume: number};
  };
}

function VolumeAnalysis({ symbol, volumeData }: VolumeAnalysisProps) {
  if (!volumeData) {
    return (
      <div className="bg-white rounded-lg p-4 shadow-lg">
        <h2 className="text-lg font-semibold mb-4">Volume Analysis</h2>
        <p className="text-gray-500">No volume data available</p>
      </div>
    );
  }

  // Color coding for volume trend
  const trendColors = {
    increasing: 'text-green-600',
    decreasing: 'text-red-600',
    neutral: 'text-gray-600'
  };

  return (
    <div className="bg-white rounded-lg p-4 shadow-lg">
      <h2 className="text-lg font-semibold mb-4">Volume Analysis - {symbol}</h2>
      
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="bg-gray-100 p-3 rounded">
          <h3 className="text-sm text-gray-600">Avg Daily Volume</h3>
          <p className="text-lg font-bold text-blue-600">
            {volumeData.avg_daily_volume.toLocaleString()}
          </p>
        </div>
        <div className="bg-gray-100 p-3 rounded">
          <h3 className="text-sm text-gray-600">Volume Trend</h3>
          <p className={`text-lg font-bold ${trendColors[volumeData.volume_trend]}`}>
            {volumeData.volume_trend.charAt(0).toUpperCase() + volumeData.volume_trend.slice(1)}
          </p>
        </div>
      </div>

      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={volumeData.daily_volume}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis 
              label={{ 
                value: 'Volume', 
                angle: -90, 
                position: 'insideLeft' 
              }}
            />
            <Tooltip 
              formatter={(value) => [value.toLocaleString(), 'Volume']}
              contentStyle={{ backgroundColor: '#f3f4f6' }}
            />
            <Area 
              type="monotone" 
              dataKey="volume" 
              stroke="#3B82F6" 
              fill="rgba(59, 130, 246, 0.2)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-4 text-sm text-gray-600">
        <p>Highest Volume Day: {volumeData.max_volume_day.date} - {volumeData.max_volume_day.volume.toLocaleString()}</p>
      </div>
    </div>
  );
}

export default VolumeAnalysis;