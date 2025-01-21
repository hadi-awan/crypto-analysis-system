import React from 'react';
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

interface CorrelationAnalysisProps {
  symbol: string;
  correlationData?: {
    correlations: Array<{
      asset: string,
      correlation_coefficient: number,
      correlation_type: 'positive' | 'negative' | 'neutral'
    }>;
  };
}

function CorrelationAnalysis({ symbol, correlationData }: CorrelationAnalysisProps) {
  if (!correlationData || !correlationData.correlations.length) {
    return (
      <div className="bg-white rounded-lg p-4 shadow-lg">
        <h2 className="text-lg font-semibold mb-4">Asset Correlation</h2>
        <p className="text-gray-500">No correlation data available</p>
      </div>
    );
  }

  // Color mapping for correlation types
  const correlationColors = {
    positive: 'text-green-600',
    negative: 'text-red-600',
    neutral: 'text-gray-600'
  };

  // Prepare scatter plot data
  const scatterData = correlationData.correlations.map(corr => ({
    ...corr,
    fill: corr.correlation_type === 'positive' ? '#10B981' : 
           corr.correlation_type === 'negative' ? '#EF4444' : '#6B7280'
  }));

  return (
    <div className="bg-white rounded-lg p-4 shadow-lg">
      <h2 className="text-lg font-semibold mb-4">Asset Correlation - {symbol}</h2>
      
      <div className="grid grid-cols-2 gap-4 mb-4">
        {correlationData.correlations.slice(0, 2).map((corr, index) => (
          <div key={index} className="bg-gray-100 p-3 rounded">
            <h3 className="text-sm text-gray-600">{corr.asset}</h3>
            <p className={`text-lg font-bold ${correlationColors[corr.correlation_type]}`}>
              {corr.correlation_coefficient.toFixed(2)}
            </p>
            <span className="text-xs text-gray-500">
              {corr.correlation_type.charAt(0).toUpperCase() + corr.correlation_type.slice(1)} Correlation
            </span>
          </div>
        ))}
      </div>

      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart>
            <CartesianGrid />
            <XAxis 
              type="number" 
              dataKey="correlation_coefficient"
              name="Correlation"
              domain={[-1, 1]}
            />
            <YAxis 
              type="category" 
              dataKey="asset"
              name="Asset"
            />
            <Tooltip 
              cursor={{ strokeDasharray: '3 3' }}
              formatter={(value, name, props) => {
                if (name === 'Correlation') {
                  return [value.toFixed(2), 'Correlation Coefficient'];
                }
                return [value, name];
              }}
            />
            <Scatter 
              data={scatterData} 
              fill="#8884d8"
            />
          </ScatterChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-4">
        <h3 className="text-sm font-semibold text-gray-600 mb-2">Correlation Insights</h3>
        <ul className="text-xs text-gray-500 space-y-1">
          {correlationData.correlations.map((corr, index) => (
            <li key={index}>
              <span className="font-medium">{corr.asset}</span>: 
              {' '}
              <span className={correlationColors[corr.correlation_type]}>
                {corr.correlation_type.charAt(0).toUpperCase() + corr.correlation_type.slice(1)} Correlation
              </span>
              {' '}
              ({corr.correlation_coefficient.toFixed(2)})
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export default CorrelationAnalysis;