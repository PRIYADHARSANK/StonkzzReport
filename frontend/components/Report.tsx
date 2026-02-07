import React, { ReactNode } from 'react';
import { ReportData, GoldPrice, GoldHistoryEntry, SilverPrice, SilverHistoryEntry } from '../services/types';
import MMIGauge from './MMIGauge';
import {
  LineChart, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer,
  BarChart, Bar, CartesianGrid, ReferenceLine
} from 'recharts';
import {
  ChevronsRight, TrendingUp, TrendingDown, Target, BarChart2, List, CheckCircle2, Zap, Activity,
  Shield, DollarSign, Briefcase, Award, Gem, ArrowRight
} from 'lucide-react';
import NiftyDashboard from './NiftyDashboard';
import HeatmapGrid from './HeatmapGrid';
import FiiDiiActivity from './FiiDiiActivity';
import TrendGauge from './TrendGauge';
import VixTrendChart from './VixTrendChart';


interface ReportProps {
  data: ReportData;
  pageToShow?: number;
}

// Internal components for styling
const Page: React.FC<{ title: string; children: ReactNode; pageNumber: number; date: string; }> = ({ title, children, pageNumber, date }) => (
  <div className="a4-page-container bg-brand-beige p-8 flex flex-col shadow-lg font-sans text-brand-black w-[800px]">
    <header className="flex justify-between items-center pb-4 border-b-2 border-brand-black">
      <div className="flex items-center gap-3">
        <img src="https://raw.githubusercontent.com/Prasannapriyan/Generator/refs/heads/main/logo.png" alt="Stonkzz Logo" className="h-16" />
        <h1 className="text-2xl font-bold font-heading">{title}</h1>
      </div>
      <p className="font-semibold font-heading">{date}</p>
    </header>
    <main className="flex-grow pt-6">
      {children}
    </main>
    <footer className="text-center text-sm font-semibold pt-4 border-t-2 border-brand-black">
      <p>www.stonkzz.com | Page {pageNumber}</p>
    </footer>
  </div>
);

const Section: React.FC<{ title: string; icon?: ReactNode; children: ReactNode }> = ({ title, icon, children }) => (
  <div className="mb-6">
    <div className="flex items-center gap-3 mb-3">
      {icon}
      <h2 className="text-2xl font-bold font-heading">{title}</h2>
    </div>
    <div className="border-2 border-brand-black rounded-lg p-4 bg-white/30">
      {children}
    </div>
  </div>
);

const Report: React.FC<ReportProps> = ({ data, pageToShow }) => {

  const getMmiZoneInfo = (value: number) => {
    if (value < 30) return { name: 'Extreme Fear', className: 'text-brand-red' };
    if (value < 50) return { name: 'Fear', className: 'text-brand-yellow' };
    if (value < 55) return { name: 'Neutral', className: 'text-slate-500' };
    if (value < 70) return { name: 'Greed', className: 'text-lime-400' };
    return { name: 'Extreme Greed', className: 'text-brand-green' };
  };

  const HighlightKeywords: React.FC<{ text: string }> = ({ text }) => {
    if (!text) return null;
    const parts = text.split(/(\*\*.*?\*\*)/g).filter(Boolean);
    return (
      <>
        {parts.map((part, index) => {
          if (part.startsWith('**') && part.endsWith('**')) {
            return <strong key={index}>{part.slice(2, -2)}</strong>;
          }
          return <span key={index}>{part}</span>;
        })}
      </>
    );
  };



  const InfoTable: React.FC<{ headers: string[], rows: (string | number)[][], highlightLast?: boolean, highlightChanges?: boolean }> = ({ headers, rows, highlightLast = false, highlightChanges = false }) => {
    const getTextColor = (cell: string | number) => {
      const s = cell.toString();
      if (s.startsWith('+')) return 'text-brand-green';
      if (s.startsWith('-')) return 'text-brand-red';
      return 'text-brand-black';
    };

    return (
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b-2 border-brand-black">
            {headers.map((h, i) => <th key={h} className={`p-2 font-bold font-heading text-brand-black ${i > 0 ? 'text-left' : ''}`}>{h}</th>)}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index} className="border-b border-brand-black/20">
              {row.map((cell, cellIndex) => {
                let textColor = 'text-brand-black';
                // Apply coloring logic based on props
                if (highlightChanges && cellIndex > 0) {
                  textColor = getTextColor(cell);
                } else if (highlightLast && cellIndex === row.length - 1) {
                  textColor = getTextColor(cell);
                }

                return (
                  <td key={cellIndex} className={`p-2 ${cellIndex === 0 ? 'font-semibold' : 'font-mono'} ${textColor}`}>
                    {cell}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    );
  };

  const GoldPage: React.FC<{ pageNumber: number }> = ({ pageNumber }) => {
    if (!data.goldData) return null;

    const GoldChangeCard: React.FC<{ karat: '24K' | '22K'; data: GoldPrice }> = ({ karat, data }) => {
      const isPositive = data.change >= 0;
      return (
        <div className="bg-emerald-50 rounded-lg p-4 border-2 border-brand-black flex flex-col justify-center items-center gap-2">
          <p className="font-bold font-heading text-2xl text-brand-black">{karat} Gold <span className="text-lg text-slate-500">/g</span></p>
          <p className="text-3xl font-bold font-mono text-brand-black">₹{data.price.toLocaleString()}</p>
          <p className={`text-lg font-semibold ${isPositive ? 'text-brand-green' : 'text-brand-red'}`}>
            {isPositive ? '+' : ''} ₹{Math.abs(data.change).toLocaleString()} {isPositive ? '▲' : '▼'}
          </p>
        </div>
      );
    };

    const GoldHistoryTable: React.FC<{ history: GoldHistoryEntry[] }> = ({ history }) => {
      const getChangeColor = (change: number) => {
        if (change > 0) return 'text-brand-green';
        if (change < 0) return 'text-brand-red';
        return 'text-brand-black';
      };
      const reversedHistory = [...history].reverse();

      return (
        <table className="w-full text-left">
          <thead>
            <tr className="border-b-2 border-brand-black">
              <th className="p-2 font-bold font-heading text-brand-black">Date</th>
              <th className="p-2 font-bold font-heading text-brand-black text-left">24K Price (₹)</th>
              <th className="p-2 font-bold font-heading text-brand-black text-left">22K Price (₹)</th>
            </tr>
          </thead>
          <tbody>
            {reversedHistory.map((item, index) => (
              <tr key={index} className="border-b border-brand-black/20">
                <td className="p-2 font-semibold text-brand-black">{item.date}</td>
                <td className="p-2 font-mono text-brand-black">
                  {item.price24k.toLocaleString()}
                  <span className={`ml-2 ${getChangeColor(item.change24k)}`}>
                    ({item.change24k >= 0 ? '+' : ''}{item.change24k})
                  </span>
                </td>
                <td className="p-2 font-mono text-brand-black">
                  {item.price22k.toLocaleString()}
                  <span className={`ml-2 ${getChangeColor(item.change22k)}`}>
                    ({item.change22k >= 0 ? '+' : ''}{item.change22k})
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      );
    };

    const formatChartDate = (date: string) => date.split(',')[0];

    return (
      <Page title="GOLD" pageNumber={pageNumber} date={data.date}>
        <Section title="Gold Rate Today (Chennai)" icon={<Award className="text-amber-500" />}>
          <div className="grid grid-cols-2 gap-4">
            <GoldChangeCard karat="24K" data={data.goldData.today24k} />
            <GoldChangeCard karat="22K" data={data.goldData.today22k} />
          </div>
        </Section>
        <Section title="Gold Rate Last 10 Days" icon={<List />}>
          <GoldHistoryTable history={data.goldData.history} />
        </Section>
        <div className="grid grid-cols-2 gap-6 mt-6">
          <Section title="24K Gold Trend" icon={<BarChart2 />}>
            <LineChart width={320} height={240} data={data.goldData.history} margin={{ top: 5, right: 20, left: -10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" strokeOpacity={0.2} />
              <XAxis dataKey="date" stroke="#1E293B" tick={{ fontFamily: 'Inter', fontSize: 12, fill: '#1E293B' }} tickFormatter={formatChartDate} />
              <YAxis stroke="#1E293B" tick={{ fontFamily: 'Inter', fontSize: 12, fill: '#1E293B' }} allowDecimals={false} domain={['auto', 'auto']} />
              <Line isAnimationActive={false} type="monotone" dataKey="price24k" name="24K Price" stroke="#FBBF24" strokeWidth={3} dot={false} />
            </LineChart>
          </Section>
          <Section title="22K Gold Trend" icon={<BarChart2 />}>
            <LineChart width={320} height={240} data={data.goldData.history} margin={{ top: 5, right: 20, left: -10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" strokeOpacity={0.2} />
              <XAxis dataKey="date" stroke="#1E293B" tick={{ fontFamily: 'Inter', fontSize: 12, fill: '#1E293B' }} tickFormatter={formatChartDate} />
              <YAxis stroke="#1E293B" tick={{ fontFamily: 'Inter', fontSize: 12, fill: '#1E293B' }} allowDecimals={false} domain={['auto', 'auto']} />
              <Line isAnimationActive={false} type="monotone" dataKey="price22k" name="22K Price" stroke="#F87171" strokeWidth={3} dot={false} />
            </LineChart>
          </Section>
        </div>
      </Page>
    );
  };

  const SilverPage: React.FC<{ pageNumber: number }> = ({ pageNumber }) => {
    if (!data.silverData) return null;

    const SilverChangeCard: React.FC<{ type: 'gram' | 'kg'; data: SilverPrice }> = ({ type, data }) => {
      const isPositive = data.change >= 0;
      const changeOptions = type === 'gram'
        ? { minimumFractionDigits: 2, maximumFractionDigits: 2 }
        : {};
      return (
        <div className="bg-emerald-50 rounded-lg p-4 border-2 border-brand-black flex flex-col justify-center items-center gap-2">
          <p className="font-bold font-heading text-2xl text-brand-black">Silver <span className="text-lg text-slate-500">/{type === 'gram' ? 'g' : 'kg'}</span></p>
          <p className="text-3xl font-bold font-mono text-brand-black">₹{data.price.toLocaleString('en-IN')}</p>
          <p className={`text-lg font-semibold ${isPositive ? 'text-brand-green' : 'text-brand-red'}`}>
            {isPositive ? '+' : ''} ₹{Math.abs(data.change).toLocaleString('en-IN', changeOptions)} {isPositive ? '▲' : '▼'}
          </p>
        </div>
      );
    };

    const SilverHistoryTable: React.FC<{ history: SilverHistoryEntry[] }> = ({ history }) => {
      const getChangeColor = (change: number) => {
        if (change >= 0) return 'text-brand-green';
        return 'text-brand-red';
      };
      const reversedHistory = [...history].reverse();
      const numberFormat = { minimumFractionDigits: 2, maximumFractionDigits: 2 };

      return (
        <table className="w-full text-left">
          <thead>
            <tr className="border-b-2 border-brand-black">
              <th className="p-2 font-bold font-heading text-brand-black">Date</th>
              <th className="p-2 font-bold font-heading text-brand-black text-left">1 gram</th>
              <th className="p-2 font-bold font-heading text-brand-black text-left">100 gram</th>
              <th className="p-2 font-bold font-heading text-brand-black text-left">1 Kg</th>
            </tr>
          </thead>
          <tbody>
            {reversedHistory.map((item, index) => (
              <tr key={index} className="border-b border-brand-black/20">
                <td className="p-2 font-semibold text-brand-black">{item.date}</td>
                <td className="p-2 font-mono text-brand-black">
                  ₹{item.price1g.toLocaleString('en-IN', numberFormat)}
                  <span className={`ml-2 ${getChangeColor(item.change1g)}`}>
                    ({item.change1g >= 0 ? '+' : ''}{item.change1g.toLocaleString('en-IN', numberFormat)})
                  </span>
                </td>
                <td className="p-2 font-mono text-brand-black">₹{item.price100g.toLocaleString('en-IN')}</td>
                <td className="p-2 font-mono text-brand-black">₹{item.price1kg.toLocaleString('en-IN')}</td>
              </tr>
            ))}
          </tbody>
        </table>
      );
    };

    const chartData = data.silverData.history.map(entry => ({
      date: entry.date,
      pricePerGram: entry.price1g
    }));

    const formatChartDate = (date: string) => date.split(',')[0];

    return (
      <Page title="SILVER" pageNumber={pageNumber} date={data.date}>
        <Section title="Silver Rate Today (Chennai)" icon={<Gem className="text-slate-500" />}>
          <div className="grid grid-cols-2 gap-4">
            <SilverChangeCard type="gram" data={data.silverData.todayGram} />
            <SilverChangeCard type="kg" data={data.silverData.todayKg} />
          </div>
        </Section>
        <Section title="Silver Rate Last 10 Days" icon={<List />}>
          <SilverHistoryTable history={data.silverData.history} />
        </Section>
        <div className="grid grid-cols-1 mt-6">
          <Section title="Silver Rate Per Gram Trend" icon={<BarChart2 />}>
            <LineChart width={700} height={240} data={chartData} margin={{ top: 5, right: 20, left: -10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" strokeOpacity={0.2} />
              <XAxis dataKey="date" stroke="#1E293B" tick={{ fontFamily: 'Inter', fontSize: 12, fill: '#1E293B' }} tickFormatter={formatChartDate} />
              <YAxis
                stroke="#1E293B"
                tick={{ fontFamily: 'Inter', fontSize: 12, fill: '#1E293B' }}
                domain={['auto', 'auto']}
                allowDecimals={false}
              />
              <Line isAnimationActive={false} type="monotone" dataKey="pricePerGram" name="Silver Price /g" stroke="#94A3B8" strokeWidth={3} dot={false} />
            </LineChart>
          </Section>
        </div>
      </Page>
    );
  };

  const LegalPage: React.FC<{ pageNumber: number }> = ({ pageNumber }) => (
    <Page title="Legal Information & Data Sources" pageNumber={pageNumber} date={data.date}>
      <div className="space-y-4">
        <Section title="Privacy" icon={<span className="text-3xl" role="img" aria-label="lock icon">🔐</span>}>
          <p className="text-xl text-slate-800 leading-relaxed">
            We value your privacy. Your personal details such as name, email, or phone number will never be shared without your explicit consent. All data is securely stored and used only to deliver the stock market updates you've subscribed to.
          </p>
        </Section>
        <Section title="Disclaimer" icon={<span className="text-3xl" role="img" aria-label="warning icon">⚠️</span>}>
          <p className="text-xl text-slate-800 leading-relaxed">
            The Stonkzz Daily Report is for informational purposes only and should not be treated as financial advice or investment recommendations. While we aim for accuracy, market data may change or include occasional errors. Always do your own research or consult a financial advisor before making decisions. We do not take responsibility for any financial outcomes.
          </p>
        </Section>
        <Section title="Terms & Conditions" icon={<span className="text-3xl" role="img" aria-label="document icon">📄</span>}>
          <p className="text-xl text-slate-800 leading-relaxed">
            By subscribing to Stonkzz, you agree to use the report for personal use only. Sharing, reselling, or redistributing is not permitted. Reports are usually delivered daily, but occasional delays may occur. A 3-day cancellation window is available after purchase. Terms may be updated anytime, and continued usage indicates your acceptance.
          </p>
        </Section>
        <Section title="Source" icon={<span className="text-3xl" role="img" aria-label="brain icon">🧠</span>}>
          <p className="text-xl text-slate-800 leading-relaxed">
            Market data is gathered from publicly available platforms like NSE, BSE, Moneycontrol, Investing.com, Trendlyne, and Sensibull. We do not conduct independent research or promote specific investments.
          </p>
        </Section>
      </div>
    </Page>
  );

  const allPages = [
    // Page 1: Nifty Glance, Nifty Tech
    <Page key="page-1" title="Stonkzz" pageNumber={1} date={data.date}>
      {data.niftyDashboardData && (
        <div className="mb-6">
          <div className="flex items-center gap-3 mb-3">
            <TrendingUp className="text-brand-black" />
            <h2 className="text-2xl font-bold font-heading">NIFTY 50 At a Glance</h2>
          </div>
          <NiftyDashboard data={data.niftyDashboardData} />
        </div>
      )}

      {data.marketVerdict && (
        <Section title="Market Verdict" icon={<Target className="text-brand-black" />}>
          <div className="bg-white p-4 rounded-lg border-l-4 border-brand-black shadow-sm">
            <h3 className="text-xl font-bold font-heading mb-2 text-brand-black border-b border-gray-200 pb-2">
              {data.marketVerdict.verdict}
            </h3>
            <p className="text-brand-black text-lg font-medium leading-relaxed">
              {data.marketVerdict.details}
            </p>
          </div>
        </Section>
      )}

      <Section title="Nifty Technical Analysis" icon={<BarChart2 className="text-brand-black" />}>
        {data.niftyTechAnalysis && typeof data.niftyTechAnalysis.trendScore === 'number' && (
          <div className="mb-6 flex justify-center">
            <TrendGauge score={data.niftyTechAnalysis.trendScore} />
          </div>
        )}
        <img src="https://raw.githubusercontent.com/Prasannapriyan/Generator/refs/heads/main/Data/nifty_chart.png" alt="Nifty Chart" className="w-full rounded-lg border-2 border-brand-black mb-4" />
        <div className="space-y-4 text-brand-black">
          {data.niftyTechAnalysis && (
            <>
              <div className="space-y-2 text-base">
                {data.niftyTechAnalysis.analysis.map((point, i) => (
                  <p key={i} className="flex items-start gap-2">
                    <ChevronsRight size={16} className="mt-1 text-slate-500 flex-shrink-0" />
                    <span><HighlightKeywords text={point} /></span>
                  </p>
                ))}
              </div>
              <div className="grid grid-cols-2 gap-6 pt-2">
                <div>
                  <h4 className="font-bold text-base mb-2 underline">Key Resistance Levels</h4>
                  <ul className="list-none space-y-1">
                    {data.niftyTechAnalysis.resistance.map((r, i) =>
                      <li key={i} className="flex items-center gap-2">
                        <Shield size={16} className="text-brand-red flex-shrink-0" />
                        <span>{r}</span>
                      </li>
                    )}
                  </ul>
                </div>
                <div>
                  <h4 className="font-bold text-base mb-2 underline">Key Support Levels</h4>
                  <ul className="list-none space-y-1">
                    {data.niftyTechAnalysis.support.map((s, i) =>
                      <li key={i} className="flex items-center gap-2">
                        <Shield size={16} className="text-brand-green flex-shrink-0" />
                        <span>{s}</span>
                      </li>
                    )}
                  </ul>
                </div>
              </div>
            </>
          )}
        </div>
      </Section>
    </Page>,

    // Page 2: MMI, Gainers/Losers
    <Page key="page-2" title="Stonkzz" pageNumber={2} date={data.date}>
      <div className="flex flex-col gap-6">
        <div className="border-2 border-brand-black rounded-lg p-3 bg-white/30">
          <h2 className="text-2xl font-bold font-heading text-center">Market Mood Index</h2>
        </div>
        <div className="border-2 border-brand-black rounded-lg p-4 bg-white flex justify-center items-center">
          <MMIGauge value={data.marketMood.current} date={data.date} />
        </div>
        <div className="flex gap-4">
          <div className="w-1/3 border-2 border-brand-black rounded-lg p-3 bg-white/30 flex flex-col justify-center">
            <h3 className="text-lg font-bold font-heading mb-2">How to read zones:</h3>
            <ul className="space-y-2 text-sm font-semibold">
              <li className="flex items-center gap-2"><div className="w-5 h-5 rounded-full bg-brand-red border-2 border-brand-black shrink-0"></div>Extreme Fear (&lt;30)</li>
              <li className="flex items-center gap-2"><div className="w-5 h-5 rounded-full bg-brand-yellow border-2 border-brand-black shrink-0"></div>Fear (30 - 50)</li>
              <li className="flex items-center gap-2"><div className="w-5 h-5 rounded-full bg-slate-400 border-2 border-brand-black shrink-0"></div>Neutral (50 - 55)</li>
              <li className="flex items-center gap-2"><div className="w-5 h-5 rounded-full bg-lime-400 border-2 border-brand-black shrink-0"></div>Greed (55 - 70)</li>
              <li className="flex items-center gap-2"><div className="w-5 h-5 rounded-full bg-brand-green border-2 border-brand-black shrink-0"></div>Extreme Greed (&gt;70)</li>
            </ul>
          </div>
          <div className="w-1/3 border-2 border-brand-black rounded-lg p-3 bg-white/30 flex flex-col">
            <h3 className="text-lg font-bold font-heading mb-2 text-center">Change Since Last Week</h3>
            <div className="flex items-center justify-around gap-2 grow">
              <div className="text-center">
                <div className="text-xs text-slate-500 font-semibold">Last Week</div>
                <div className={`text-2xl font-bold font-mono ${getMmiZoneInfo(data.marketMood.previous).className}`}>{data.marketMood.previous.toFixed(2)}</div>
                <div className={`text-sm font-semibold ${getMmiZoneInfo(data.marketMood.previous).className}`}>({getMmiZoneInfo(data.marketMood.previous).name})</div>
              </div>
              <ArrowRight className="w-6 h-6 text-brand-black mt-4 shrink-0" />
              <div className="text-center">
                <div className="text-xs text-slate-500 font-semibold">This Week</div>
                <div className={`text-2xl font-bold font-mono ${getMmiZoneInfo(data.marketMood.current).className}`}>{data.marketMood.current.toFixed(2)}</div>
                <div className={`text-sm font-semibold ${getMmiZoneInfo(data.marketMood.current).className}`}>({getMmiZoneInfo(data.marketMood.current).name})</div>
              </div>
            </div>
          </div>
          {data.marketMood.niftyChange &&
            <div className="w-1/3 border-2 border-brand-black rounded-lg p-3 bg-white/30 flex flex-col">
              <h3 className="text-lg font-bold font-heading mb-2 text-center">Change in NIFTY</h3>
              <div className="flex items-center justify-around gap-2 grow">
                <div className="text-center">
                  <div className="text-xs text-slate-500 font-semibold">Points</div>
                  <div className={`text-2xl font-bold font-mono ${data.marketMood.niftyChange.value >= 0 ? 'text-brand-green' : 'text-brand-red'}`}>
                    {data.marketMood.niftyChange.value > 0 ? '+' : ''}{data.marketMood.niftyChange.value.toFixed(2)}
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-xs text-slate-500 font-semibold"> % Change</div>
                  <div className={`text-2xl font-bold font-mono ${data.marketMood.niftyChange.value >= 0 ? 'text-brand-green' : 'text-brand-red'}`}>
                    {data.marketMood.niftyChange.value > 0 ? '+' : ''}{data.marketMood.niftyChange.percentage}
                  </div>
                </div>
              </div>
            </div>
          }
        </div>
        <div className="border-2 border-brand-black rounded-lg p-4 bg-white/30">
          <h3 className="text-xl font-bold font-heading mb-3">Analysis:</h3>
          <div className="space-y-3">
            {data.marketMood.analysis.map((point, index) => (
              <div key={index} className="flex items-start gap-3">
                <ChevronsRight className="text-slate-500 mt-1 flex-shrink-0" size={20} />
                <p className="text-base text-slate-800 leading-relaxed"><HighlightKeywords text={point} /></p>
              </div>
            ))}
          </div>
        </div>
      </div>
      <div className="flex gap-6 mt-6">
        <div className="w-1/2">
          <Section title="Top Gainers" icon={<TrendingUp className="text-brand-green" />}>
            <InfoTable
              headers={['Stock', 'Price', 'Change (%)']}
              rows={data.niftyMovers.topGainers.map(s => [s.name, s.value, s.change])}
              highlightLast={true}
            />
          </Section>
        </div>
        <div className="w-1/2">
          <Section title="Top Losers" icon={<TrendingDown className="text-brand-red" />}>
            <InfoTable
              headers={['Stock', 'Price', 'Change (%)']}
              rows={data.niftyMovers.topLosers.map(s => [s.name, s.value, s.change])}
              highlightLast={true}
            />
          </Section>
        </div>
      </div>
    </Page>,

    // Page 3: Nifty OI/PCR
    <Page key="page-3" title="Stonkzz" pageNumber={3} date={data.date}>
      <Section title="Nifty Open Interest Analysis" icon={<Target className="text-brand-black" />}>
        {data.realTimeOiData?.summary?.timestamp && (
          <div className={`mb-3 px-3 py-2 rounded-md border text-sm font-semibold flex items-center gap-2 ${data.realTimeOiData.summary.timestamp.includes('Synthetic')
            ? 'bg-amber-100 border-amber-400 text-amber-800'
            : 'bg-emerald-100 border-emerald-400 text-emerald-800'
            }`}>
            {data.realTimeOiData.summary.timestamp.includes('Synthetic') ? (
              <>
                <Shield size={16} className="text-amber-600" />
                <span>⚠️ Using Estimated Data (Live Sources Unavailable)</span>
              </>
            ) : (
              <>
                <CheckCircle2 size={16} className="text-emerald-600" />
                <span>✅ Live Market Data Active ({data.realTimeOiData.summary.timestamp})</span>
              </>
            )}
          </div>
        )}
        {data.realTimeOiData && data.realTimeOiData.oi_chart_data ? (
          <div className="h-64 w-full mb-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.realTimeOiData.oi_chart_data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} opacity={0.3} />
                <XAxis dataKey="strike" tick={{ fontSize: 10, fill: '#333', fontWeight: 'bold' }} />
                <YAxis tickFormatter={(val) => (val / 100000).toFixed(0) + 'L'} tick={{ fontSize: 10, fill: '#333' }} />
                <Tooltip
                  formatter={(value: number, name: string) => [(value / 100000).toFixed(2) + 'L', name]}
                  labelStyle={{ color: 'black', fontWeight: 'bold' }}
                  contentStyle={{ borderRadius: '8px', border: '1px solid #ccc' }}
                />
                <Legend wrapperStyle={{ fontSize: '12px' }} />
                <Bar dataKey="call_oi" name="Call OI (Resistance)" fill="#ef4444" radius={[4, 4, 0, 0]} barSize={15} />
                <Bar dataKey="put_oi" name="Put OI (Support)" fill="#22c55e" radius={[4, 4, 0, 0]} barSize={15} />
                <ReferenceLine x={data.realTimeOiData.summary.spot} stroke="#2563eb" strokeDasharray="3 3" label={{ value: 'Spot', position: 'top', fill: '#2563eb', fontSize: 10 }} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <img
            src="https://raw.githubusercontent.com/Prasannapriyan/Generator/refs/heads/main/Data/nifty_oi_chart.png"
            alt="Nifty OI Chart"
            className="w-full rounded-lg border-2 border-brand-black"
          />
        )}

        <div className="mt-4 space-y-3 text-sm text-brand-black leading-relaxed">
          {data.realTimeOiData && data.realTimeOiData.analysis_points && data.realTimeOiData.analysis_points.length > 0 ? (
            data.realTimeOiData.analysis_points.map((point, i) => (
              <p key={i} className="flex items-start gap-2">
                <span className="text-xl font-bold text-brand-red leading-none mt-0">»</span>
                <span>{point}</span>
              </p>
            ))
          ) : (
            data.niftyOiAnalysis.summary.map((item, i) => (
              <p key={i} className="flex items-start gap-2">
                <ChevronsRight size={16} className="mt-1 text-slate-500 flex-shrink-0" />
                <span><HighlightKeywords text={item} /></span>
              </p>
            ))
          )}
        </div>
      </Section>

      <Section title="NIFTY50 PCR Data" icon={<Target className="text-brand-black" />}>
        {data.realTimeOiData && data.realTimeOiData.pcr_trend_data && data.realTimeOiData.pcr_trend_data.length > 0 ? (
          <div className="h-64 w-full mb-4">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data.realTimeOiData.pcr_trend_data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" tick={{ fontSize: 10 }} />
                <YAxis domain={[0.5, 1.5]} tick={{ fontSize: 10 }} label={{ value: 'PCR', angle: -90, position: 'insideLeft' }} />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="pcr" stroke="#8884d8" strokeWidth={2} dot={true} name="PCR Trend" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <img
            src="https://raw.githubusercontent.com/Prasannapriyan/Generator/refs/heads/main/Data/pcr.png"
            alt="NIFTY50 PCR Chart"
            className="w-full rounded-lg border-2 border-brand-black"
          />
        )}

        <div className="mt-4 space-y-2 text-base text-brand-black">
          {data.realTimeOiData ? (
            <>
              <p className="flex items-start gap-2">
                <ChevronsRight size={16} className="mt-1 text-slate-500 flex-shrink-0" />
                <span>
                  Current PCR is <strong>{data.realTimeOiData.summary.pcr}</strong> with Total Put OI at <strong>{data.realTimeOiData.summary.put_oi.toLocaleString()}</strong> and Total Call OI at <strong>{data.realTimeOiData.summary.call_oi.toLocaleString()}</strong>.
                </span>
              </p>
              {/* Check if we have analysis points specific to PCR in realTimeOiData, otherwise show generic message */}
              <p className="italic text-sm text-slate-600">Real-time trend available above. Refer to OI Analysis section for detailed sentiment.</p>
            </>
          ) : (
            data.niftyPcrAnalysis && (
              <>
                <p className="flex items-start gap-2">
                  <ChevronsRight size={16} className="mt-1 text-slate-500 flex-shrink-0" />
                  <span>
                    Current PCR is <strong>{data.niftyPcrAnalysis.rawData.pcr}</strong> with Total Put OI at <strong>{data.niftyPcrAnalysis.rawData.putOi}</strong> and Total Call OI at <strong>{data.niftyPcrAnalysis.rawData.callOi}</strong>.
                  </span>
                </p>
                <p className="flex items-start gap-2">
                  <ChevronsRight size={16} className="mt-1 text-slate-500 flex-shrink-0" />
                  <span><HighlightKeywords text={data.niftyPcrAnalysis.summary} /></span>
                </p>
              </>
            ))}
        </div>
      </Section>
    </Page>,

    // Page 4: Heatmap
    <Page key="page-4" title="Stonkzz" pageNumber={4} date={data.date}>
      <div className="flex flex-col h-full">
        <div className="flex items-center gap-3 mb-3">
          <BarChart2 className="text-brand-black" />
          <h2 className="text-2xl font-bold font-heading">NIFTY50 Heatmap</h2>
        </div>
        <div className="flex-grow flex justify-center items-center w-full">
          {data.heatmapStocks && data.heatmapStocks.length > 0 ? (
            <HeatmapGrid stocks={data.heatmapStocks} />
          ) : (
            <img
              src="https://raw.githubusercontent.com/Prasannapriyan/Generator/refs/heads/main/Data/heatmap.png"
              alt="NIFTY50 Heatmap"
              className="w-full rounded-lg border-2 border-brand-black"
            />
          )}
        </div>
        {data.heatmapAnalysis && (
          <div className="mt-6">
            <Section title="Heatmap Analysis" icon={<List className="text-brand-black" />}>
              <ul className="space-y-3">
                {data.heatmapAnalysis.map((item, i) => (
                  <li key={i} className="flex items-start gap-3">
                    <ChevronsRight className="text-slate-500 mt-1 flex-shrink-0" size={20} />
                    <span className="text-brand-black text-base"><HighlightKeywords text={item} /></span>
                  </li>
                ))}
              </ul>
            </Section>
          </div>
        )}
      </div>
    </Page>,

    // Page 5: Market Bulletin, Key Stocks
    <Page key="page-5" title="Stonkzz" pageNumber={5} date={data.date}>
      <Section title="Market Bulletin" icon={<List className="text-brand-black" />}>
        <ul className="space-y-3">
          {data.marketBulletin.slice(0, 4).map((item, i) => (
            <li key={i} className="flex items-start gap-3">
              <CheckCircle2 className="text-brand-green mt-1 flex-shrink-0" size={20} />
              <span className="text-brand-black">
                {item.length > 85 ? item.substring(0, 85) + '...' : item}
              </span>
            </li>
          ))}
        </ul>
      </Section>
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-3">
          <Zap className="text-brand-black" />
          <h2 className="text-2xl font-bold font-heading">Key Stocks to Watch</h2>
        </div>
        {/* Fixed Height Container to Ensure Visibility */}
        <div className="min-h-[200px] grid grid-cols-2 gap-6">
          <div className="border-2 border-brand-black rounded-lg p-4 bg-white/30">
            {data.keyStocksPage3?.positive?.length > 0 ? (
              <InfoTable
                headers={['Stock', 'Change (%)']}
                rows={data.keyStocksPage3.positive.map(s => [s.name, s.change])}
                highlightLast={true}
              />
            ) : (
              <div className="text-center text-slate-500 italic p-4">No Positive Trends</div>
            )}
          </div>
          <div className="border-2 border-brand-black rounded-lg p-4 bg-white/30">
            {data.keyStocksPage3?.negative?.length > 0 ? (
              <InfoTable
                headers={['Stock', 'Change (%)']}
                rows={data.keyStocksPage3.negative.map(s => [s.name, s.change])}
                highlightLast={true}
              />
            ) : (
              <div className="text-center text-slate-500 italic p-4">No Negative Trends</div>
            )}
          </div>
        </div>
      </div>
    </Page>,

    // Page 6: FII/DII
    <Page key="page-6" title="Stonkzz" pageNumber={6} date={data.date}>
      <Section title="" icon={<Briefcase className="text-brand-black" />}>
        {/* Title handled inside component */}
        <FiiDiiActivity data={data.fiiDiiActivity} />
      </Section>

    </Page>,

    // NEW Page 7 (was page 10): VIX, 52W High/Low
    <Page key="page-7" title="Stonkzz" pageNumber={7} date={data.date}>
      <Section title="India VIX Analysis" icon={<BarChart2 />}>
        {data.vixAnalysis && (
          <>
            {data.vixAnalysis.history && data.vixAnalysis.history.length > 0 ? (
              <VixTrendChart data={data.vixAnalysis.history} />
            ) : (
              <img
                src="https://raw.githubusercontent.com/Prasannapriyan/Generator/refs/heads/main/Data/vix.png"
                alt="India VIX Chart"
                className="w-full rounded-lg border-2 border-brand-black"
              />
            )}
            <div className="mt-4 space-y-2 text-base text-brand-black">
              <p className="flex items-start gap-2">
                <ChevronsRight size={16} className="mt-1 text-slate-500 flex-shrink-0" />
                <span>
                  Current VIX is <strong>{data.vixAnalysis.rawData.value}</strong>, with a change of <strong>{data.vixAnalysis.rawData.change}</strong>.
                </span>
              </p>
              <p className="flex items-start gap-2">
                <ChevronsRight size={16} className="mt-1 text-slate-500 flex-shrink-0" />
                <span><HighlightKeywords text={data.vixAnalysis.summary} /></span>
              </p>
            </div>
          </>
        )}
      </Section>
      {data.highLowData && (
        <div className="grid grid-cols-2 gap-6 mt-6">
          <Section title="52W High" icon={<TrendingUp className="text-brand-green" />}>
            <InfoTable
              headers={['Stock', 'Price', 'Change %']}
              rows={data.highLowData.highs.map(stock => [stock.name, `₹${stock.price}`, `+${stock.change.replace('%', '')}%`])}
              highlightChanges={true}
            />
          </Section>
          <Section title="52W Low" icon={<TrendingDown className="text-brand-red" />}>
            <InfoTable
              headers={['Stock', 'Price', 'Change %']}
              rows={data.highLowData.lows.map(stock => [stock.name, `₹${stock.price}`, `${stock.change}`])}
              highlightChanges={true}
            />
          </Section>
        </div>
      )}
    </Page>,

    // NEW Page 8 (was page 7): Global, Currency
    <Page key="page-8" title="Stonkzz" pageNumber={8} date={data.date}>
      <Section title="Key Global Indices" icon={<Briefcase className="text-brand-black" />}>
        <InfoTable
          headers={['Name', 'LTP', 'Change', 'Change %']}
          rows={data.globalIndices.map(s => [`${s.country ? s.country + ' ' : ''}${s.name}`, s.ltp, s.change, s.changePercent])}
          highlightChanges={true}
        />
      </Section>
      <Section title="Global Currency Data" icon={<DollarSign className="text-brand-black" />}>
        <InfoTable
          headers={['Currency', 'Name', 'Country', 'Value (in INR)']}
          rows={data.globalCurrencies.map(c => [
            `${c.countryFlag} ${c.code}`,
            c.name,
            c.countryName,
            `₹${c.value.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
          ])}
        />
      </Section>
      <Section title="GIFT Nifty 50" icon={<Activity className="text-brand-black" />}>
        {data.giftNiftyData ? (
          <div className="bg-white/50 rounded-xl p-4 border border-brand-black/10">
            <div className="flex justify-between items-center mb-4">
              <div>
                <div className="text-3xl font-bold font-mono text-brand-black">
                  ₹{data.giftNiftyData.last_price.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                </div>
                <div className={`text-lg font-bold flex items-center gap-1 ${data.giftNiftyData.change >= 0 ? 'text-brand-green' : 'text-brand-red'}`}>
                  {data.giftNiftyData.change >= 0 ? <TrendingUp size={20} /> : <TrendingDown size={20} />}
                  {data.giftNiftyData.change > 0 ? '+' : ''}{data.giftNiftyData.change.toFixed(2)} ({data.giftNiftyData.change_percent.toFixed(2)}%)
                </div>
              </div>
              <div className="text-right text-xs text-slate-500">
                <div>Source: {data.giftNiftyData.timestamp}</div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="bg-white p-3 rounded-lg border border-slate-200">
                <div className="text-xs text-slate-500 uppercase tracking-wider mb-1">Open</div>
                <div className="font-mono font-bold">{data.giftNiftyData.open ? data.giftNiftyData.open.toLocaleString() : 'N/A'}</div>
              </div>
              <div className="bg-white p-3 rounded-lg border border-slate-200">
                <div className="text-xs text-slate-500 uppercase tracking-wider mb-1">Previous Close</div>
                <div className="font-mono font-bold">{data.giftNiftyData.prev_close ? data.giftNiftyData.prev_close.toLocaleString() : 'N/A'}</div>
              </div>
              <div className="bg-white p-3 rounded-lg border border-slate-200">
                <div className="text-xs text-slate-500 uppercase tracking-wider mb-1">High</div>
                <div className="font-mono font-bold text-brand-green">{data.giftNiftyData.high ? data.giftNiftyData.high.toLocaleString() : 'N/A'}</div>
              </div>
              <div className="bg-white p-3 rounded-lg border border-slate-200">
                <div className="text-xs text-slate-500 uppercase tracking-wider mb-1">Low</div>
                <div className="font-mono font-bold text-brand-red">{data.giftNiftyData.low ? data.giftNiftyData.low.toLocaleString() : 'N/A'}</div>
              </div>
              <div className="bg-white p-3 rounded-lg border border-slate-200">
                <div className="text-xs text-slate-500 uppercase tracking-wider mb-1">52W High</div>
                <div className="font-mono font-bold text-brand-green">{data.giftNiftyData.week_52_high ? data.giftNiftyData.week_52_high.toLocaleString() : 'N/A'}</div>
              </div>
              <div className="bg-white p-3 rounded-lg border border-slate-200">
                <div className="text-xs text-slate-500 uppercase tracking-wider mb-1">52W Low</div>
                <div className="font-mono font-bold text-brand-red">{data.giftNiftyData.week_52_low ? data.giftNiftyData.week_52_low.toLocaleString() : 'N/A'}</div>
              </div>
            </div>
          </div>
        ) : (
          <div className="text-center p-6 text-slate-500">
            GIFT Nifty Data Unavailable
          </div>
        )}
      </Section>
    </Page>,

    // NEW Page 9 (was page 8): Gold
    <GoldPage key="page-9" pageNumber={9} />,

    // NEW Page 10 (was page 9): Silver
    <SilverPage key="page-10" pageNumber={10} />,

    // Page 11: Terms and Conditions
    <Page key="page-11" title="Terms & Conditions" pageNumber={11} date={data.date}>
      <div className="flex flex-col gap-6">
        <div className="border-2 border-brand-black rounded-lg p-6 bg-white/50">
          <div className="flex items-center gap-3 mb-6">
            <Shield size={32} className="text-brand-black" />
            <h2 className="text-2xl font-bold font-heading">Important Disclaimer</h2>
          </div>

          <div className="space-y-4 text-brand-black font-medium leading-relaxed">
            <p>
              <strong>1. Educational Purpose Only:</strong> The content provided in this report, generated by Stonkzz, is strictly for educational and informational purposes. It does not constitute financial, investment, or trading advice.
            </p>

            <p>
              <strong>2. No Recommendation:</strong> None of the information contained here is a recommendation to buy, sell, or hold any security, financial product, or instrument. Stonkzz and its creators are not SEBI registered research analysts or advisors.
            </p>

            <p>
              <strong>3. Market Risk:</strong> Stock market trading and investing involve inherent risks, including the potential loss of capital. Past performance is not indicative of future results. You are solely responsible for your investment decisions.
            </p>

            <p>
              <strong>4. Data Accuracy:</strong> While we strive to provide accurate and up-to-date data, Stonkzz relies on third-party sources and algorithms which may differ from real-time market data. We do not guarantee the completeness or accuracy of the information.
            </p>

            <p>
              <strong>5. Liability:</strong> Stonkzz, its developers, and affiliates shall not be held liable for any direct, indirect, or consequential damages resulting from the use of this report.
            </p>
          </div>
        </div>

        <div className="border-2 border-brand-black rounded-lg p-6 bg-brand-yellow/20 flex items-center justify-center text-center">
          <p className="text-brand-black font-bold text-lg">
            By using this report, you acknowledge that you have read, understood, and agreed to these terms.
          </p>
        </div>

        <div className="mt-8 flex justify-center">
          <img src="https://raw.githubusercontent.com/Prasannapriyan/Generator/refs/heads/main/logo.png" alt="Stonkzz Logo" className="h-24 opacity-80 grayscale hover:grayscale-0 transition-all" />
        </div>
      </div>
    </Page>,

    // End of pages
  ];

  if (pageToShow) {
    // This is used by the PDF generator to render one page at a time.
    return allPages[pageToShow - 1] || null;
  }

  // This is used for the live preview, rendering all pages.
  return <>{allPages}</>;
};

export default Report;