import React from 'react';
import { HeatmapStock } from '../services/types';

interface HeatmapGridProps {
    stocks: HeatmapStock[];
}

const HeatmapGrid: React.FC<HeatmapGridProps> = ({ stocks }) => {
    // Sort by Change descending (Green to Red) for clear visual trend
    const sortedStocks = [...stocks].sort((a, b) => b.change - a.change);

    const getColor = (change: number) => {
        if (change === 0) return 'bg-gray-200 text-gray-800';
        const absChange = Math.abs(change);

        // Green Shades
        if (change > 0) {
            if (absChange >= 3) return 'bg-emerald-700 text-white';
            if (absChange >= 2) return 'bg-emerald-600 text-white';
            if (absChange >= 1) return 'bg-emerald-500 text-white';
            if (absChange >= 0.5) return 'bg-emerald-400 text-brand-black';
            return 'bg-emerald-200 text-brand-black';
        }
        // Red Shades
        else {
            if (absChange >= 3) return 'bg-red-700 text-white';
            if (absChange >= 2) return 'bg-red-600 text-white';
            if (absChange >= 1) return 'bg-red-500 text-white';
            if (absChange >= 0.5) return 'bg-red-400 text-brand-black';
            return 'bg-red-200 text-brand-black';
        }
    };

    return (
        <div className="grid grid-cols-5 md:grid-cols-8 gap-1 w-full h-full rounded-lg border-2 border-brand-black bg-white p-2">
            {sortedStocks.map((stock) => (
                <div
                    key={stock.symbol}
                    className={`${getColor(stock.change)} flex flex-col justify-center items-center p-1 text-center transition-all hover:opacity-90 rounded-sm border border-black/5 aspect-square sm:aspect-auto`}
                >
                    <span className="font-bold text-[0.55rem] sm:text-[0.7rem] leading-tight w-full px-0.5 whitespace-normal break-words">{stock.name || stock.symbol}</span>
                    <span className="text-[0.6rem] sm:text-xs font-mono font-bold mt-1">
                        {stock.change > 0 ? '+' : ''}{stock.change.toFixed(2)}%
                    </span>
                    <span className="text-[0.5rem] mt-0.5 opacity-80">
                        {Math.round(stock.value)}
                    </span>
                </div>
            ))}
        </div>
    );
};

export default HeatmapGrid;
