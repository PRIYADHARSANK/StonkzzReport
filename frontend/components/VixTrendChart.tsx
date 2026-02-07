import React from 'react';
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer
} from 'recharts';
import { VixHistoryPoint } from '../services/types';

interface VixTrendChartProps {
    data: VixHistoryPoint[];
}

const VixTrendChart: React.FC<VixTrendChartProps> = ({ data }) => {
    if (!data || data.length === 0) return null;

    const formatDate = (dateStr: string) => {
        // Expect YYYY-MM-DD
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });
    };

    return (
        <div className="w-full h-72 bg-white rounded-lg p-4 border-2 border-brand-black shadow-neobrutalism">
            <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 10 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#ccc" strokeOpacity={0.3} vertical={false} />
                    <XAxis
                        dataKey="date"
                        tickFormatter={formatDate}
                        stroke="#000"
                        tick={{ fontSize: 11, fontWeight: 'bold' }}
                        interval={Math.ceil(data.length / 8)} // Show ~8 ticks evenly
                        axisLine={{ stroke: '#000', strokeWidth: 2 }}
                        tickLine={false}
                        dy={10}
                    />
                    <YAxis
                        stroke="#000"
                        domain={['auto', 'auto']}
                        tick={{ fontSize: 11, fontWeight: 'bold' }}
                        axisLine={{ stroke: '#000', strokeWidth: 2 }}
                        tickLine={false}
                        dx={-5}
                    />
                    <Tooltip
                        labelFormatter={(label) => formatDate(label)}
                        contentStyle={{
                            backgroundColor: '#fff',
                            borderRadius: '8px',
                            border: '2px solid #000',
                            boxShadow: '4px 4px 0px 0px rgba(0,0,0,1)'
                        }}
                    />
                    <Line
                        type="monotone"
                        dataKey="value"
                        stroke="#ef4444"
                        strokeWidth={3}
                        dot={{ r: 3, strokeWidth: 2, fill: '#fff', stroke: '#ef4444' }}
                        activeDot={{ r: 6, strokeWidth: 2, fill: '#ef4444', stroke: '#000' }}
                        isAnimationActive={true}
                    />
                </LineChart>
            </ResponsiveContainer>
        </div>
    );
};

export default VixTrendChart;
