import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, Cell } from 'recharts';
import { OpenInterestData } from '../services/types';

interface OpenInterestChartProps {
  data: OpenInterestData[];
}

const OpenInterestChart: React.FC<OpenInterestChartProps> = ({ data }) => {
  return (
    <div className="w-full h-80 bg-white/50 p-4 rounded-lg border-2 border-brand-black flex justify-center items-center">
      <BarChart
        width={700}
        height={300}
        data={data}
        margin={{
          top: 5,
          right: 20,
          left: 10,
          bottom: 5,
        }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" strokeOpacity={0.2} />
        <XAxis dataKey="strike" stroke="#1E293B" tick={{ fontFamily: 'Inter', fontSize: 12 }} />
        <YAxis stroke="#1E293B" tick={{ fontFamily: 'Inter', fontSize: 12 }} />
        <Tooltip
          contentStyle={{
            backgroundColor: '#FDF6E9',
            border: '2px solid #1E293B',
            borderRadius: '0.5rem',
            fontFamily: 'Inter',
            color: '#1E293B',
          }}
        />
        <Legend wrapperStyle={{ fontFamily: 'Inter', fontSize: '14px', color: '#1E293B' }} />
        <Bar isAnimationActive={false} dataKey="putOI" name="Put OI" stackId="a">
           {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.putIncrease ? '#F87171' : '#FCA5A5'} />
          ))}
        </Bar>
        <Bar isAnimationActive={false} dataKey="callOI" name="Call OI" stackId="b">
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.callIncrease ? '#34D399' : '#6EE7B7'} />
          ))}
        </Bar>
      </BarChart>
    </div>
  );
};

export default OpenInterestChart;