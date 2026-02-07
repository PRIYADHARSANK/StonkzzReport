import React from 'react';
import { NiftyDashboardData } from '../services/types';

interface RangeSliderProps {
  low: number;
  high: number;
  current: number;
  label: string;
}

const RangeSlider: React.FC<RangeSliderProps> = ({ low, high, current, label }) => {
  const percentage = high > low ? ((current - low) / (high - low)) * 100 : 50;
  const safePercentage = Math.max(0, Math.min(100, percentage));

  const currentFormatted = current.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const lowFormatted = low.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const highFormatted = high.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  return (
    <div className="w-full">
      <h3 className="font-bold text-lg mb-4">{label}</h3>
      <div className="relative h-2 w-full">
        <div className="absolute top-1/2 -translate-y-1/2 w-full h-1.5 bg-gradient-to-r from-red-400 via-yellow-300 to-green-400 rounded-full"></div>
        <div 
          className="absolute top-1/2 -translate-y-1/2" 
          style={{ left: `calc(${safePercentage}% - 10px)` }}
        >
          <div className="relative flex justify-center">
            <div className="absolute -top-10">
              <div className="px-2 py-1 bg-gray-800 text-white text-xs font-bold rounded shadow-lg whitespace-nowrap">
                {currentFormatted}
              </div>
              <div className="absolute top-full left-1/2 -translate-x-1/2 w-0 h-0 border-x-4 border-x-transparent border-t-[4px] border-t-gray-800"></div>
            </div>
            <div className="w-5 h-5 bg-white rounded-full border-2 border-gray-400 shadow"></div>
          </div>
        </div>
      </div>
      <div className="flex justify-between items-center mt-3 text-sm">
        <div>
          <span className="text-slate-500">Low</span>
          <p className="font-semibold">{lowFormatted}</p>
        </div>
        <div className="text-right">
          <span className="text-slate-500">High</span>
          <p className="font-semibold">{highFormatted}</p>
        </div>
      </div>
    </div>
  );
};


const NiftyDashboard: React.FC<{ data: NiftyDashboardData }> = ({ data }) => {
  if (!data) return null;

  const isZero = parseFloat(data.changeValue.replace(/,/g, '')) === 0;

  const changeColor = isZero
    ? 'text-slate-500' // Neutral color for zero change
    : data.isPositive ? 'text-green-500' : 'text-red-500';

  const ChangeIcon = isZero
    ? null
    : data.isPositive ? '↑' : '↓';

  return (
    <div className="bg-[#FBF5EB] border-2 border-[#E7D8C9] rounded-lg p-4 font-sans text-brand-black">
      {/* Top section: Title, Current Price and Change */}
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-bold">NIFTY 50</h2>
        <div className="flex items-baseline gap-4">
          <span className="text-2xl font-bold font-mono">₹{data.currentValue}</span>
          <div className={`flex items-center gap-1 font-bold ${changeColor}`}>
            {ChangeIcon && <span className="text-xl leading-none font-sans">{ChangeIcon}</span>}
            <span>{data.changeValue} ({data.changePercent})</span>
          </div>
        </div>
      </div>

      <hr className="border-t border-[#E7D8C9] my-3" />

      {/* Mid section: Prev Close, Open, Volume */}
      <div className="grid grid-cols-3 gap-4 text-center">
        <div>
          <p className="text-sm text-slate-500">Prev. Close</p>
          <p className="font-semibold text-lg">{data.prevClose}</p>
        </div>
        <div>
          <p className="text-sm text-slate-500">Open</p>
          <p className="font-semibold text-lg">₹{data.open}</p>
        </div>
        <div>
          <p className="text-sm text-slate-500">Volume (Lakhs)</p>
          <p className="font-semibold text-lg">{data.volume}</p>
        </div>
      </div>

      {/* Bottom section: Sliders */}
      <div className="flex gap-8 mt-6">
        <div className="w-1/2">
          <RangeSlider 
              label="52 Week"
              low={data.week52.low}
              high={data.week52.high}
              current={data.week52.current}
          />
        </div>
        <div className="w-1/2">
          <RangeSlider 
              label="Intraday"
              low={data.intraday.low}
              high={data.intraday.high}
              current={data.intraday.current}
          />
        </div>
      </div>
    </div>
  );
};

export default NiftyDashboard;