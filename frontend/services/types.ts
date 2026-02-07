// import { FiiDiiData } from './fiiDiiService';
// import { GiftNiftyData } from './giftNiftyService';
import { GiftNiftyData } from './giftNiftyService';
// Re-defining or importing correctly. 
// Ideally define basic types here.

export interface FiiDiiData {
  period: string;
  fii: number;
  dii: number;
}

export interface StockInfo {
  name: string;
  value: number | string;
  change: string;
}

export interface NiftyMoversData {
  topGainers: StockInfo[];
  topLosers: StockInfo[];
}

export interface SectorInfo {
  name: string;
  change: string;
}

export interface VolumeShocker {
  name: string;
  cmp: number;
}

export interface IndexData {
  name: string;
  country?: string;
  ltp: string;
  change: string;
  changePercent: string;
}

export interface CurrencyData {
  code: string;
  name: string;
  countryName: string;
  countryFlag: string;
  value: number;
}

export interface OpenInterestData {
  strike: number;
  putOI: number;
  putIncrease: boolean;
  callOI: number;
  callIncrease: boolean;
}

export interface FiiDiiData {
  date: string;
  fii: number;
  dii: number;
}

export interface FiiDiiSummary {
  fii: number;
  dii: number;
}

export interface FiiDiiResponse {
  daily_data: FiiDiiData[];
  summary: {
    last_7_days: FiiDiiSummary;
    last_10_days: FiiDiiSummary;
  };
}

export interface BuildUpData {
  name: string;
  change: string;
}

export interface KeyStockWatch {
  name: string;
  change: string;
}

export interface KeyStocksPage3 {
  positive: KeyStockWatch[];
  negative: KeyStockWatch[];
}

export interface GoldPrice {
  price: number;
  change: number;
}

export interface GoldHistoryEntry {
  date: string;
  price24k: number;
  change24k: number;
  price22k: number;
  change22k: number;
}

export interface GoldData {
  today24k: GoldPrice;
  today22k: GoldPrice;
  history: GoldHistoryEntry[];
}

export interface SilverPrice {
  price: number;
  change: number;
}

export interface SilverHistoryEntry {
  date: string;
  price1g: number;
  change1g: number;
  price100g: number;
  price1kg: number;
}

export interface SilverData {
  todayGram: SilverPrice;
  todayKg: SilverPrice;
  history: SilverHistoryEntry[];
}

export interface PcrData {
  rawData: {
    pcr: string;
    putOi: string;
    callOi: string;
  };
  summary: string;
}

export interface VixHistoryPoint {
  date: string;
  value: number;
}

export interface VixData {
  rawData: {
    value: string;
    change: string;
  };
  summary: string;
  history?: VixHistoryPoint[]; // Added history
}

export interface NiftyChange {
  value: number;
  percentage: string;
}

export interface MmiData {
  current: number;
  previous: number;
  analysis: string[];
  niftyChange: NiftyChange;
}

export interface NiftyDashboardData {
  name: string;
  currentValue: string;
  changeValue: string;
  changePercent: string;
  isPositive: boolean;
  prevClose: string;
  open: string;
  volume: string;
  week52: { low: number; high: number; current: number; };
  intraday: { low: number; high: number; current: number; };
}

export interface HighLowStockInfo {
  name: string;
  price: string;
  change: string;
  value: string;
}

export interface HighLowData {
  highs: HighLowStockInfo[];
  lows: HighLowStockInfo[];
}

export interface HeatmapStock {
  symbol: string;
  name?: string; // Added optional
  value: number;
  change: number;
}

export interface OiChartPoint {
  strike: number;
  call_oi: number;
  put_oi: number;
}

export interface PcrTrendPoint {
  time: string;
  pcr: number;
  spot: number;
}

export interface NiftyOiAnalysisData {
  summary: {
    spot: number;
    pcr: number;
    call_oi: number;
    put_oi: number;
    support: number;
    resistance: number;
    timestamp: string;
  };
  analysis_points: string[];
  oi_chart_data: OiChartPoint[];
  pcr_trend_data: PcrTrendPoint[];
}

export interface ReportData {
  date: string;
  marketMood: MmiData;
  niftyMovers: NiftyMoversData;
  sectorAnalysis: SectorInfo[];
  globalIndices: IndexData[];
  globalCurrencies: CurrencyData[];
  marketBulletin: string[];
  keyStocksPage3: KeyStocksPage3;
  niftyTechAnalysis: {
    analysis: string[];
    resistance: string[];
    support: string[];
    trendScore?: number; // Added for real-time gauge
  };
  niftyDashboardData: NiftyDashboardData;
  niftyOiAnalysis: {
    summary: string[];
  };
  bankNiftyTechAnalysis: {
    daily: string;
    hourly: string;
    resistance: string[];
    support: string[];
    trendScore?: number;
  };
  niftyPcrAnalysis: PcrData;
  stocksInFnoBan: string[];
  stocksRemovedFromFnoBan: string[];
  fiiDiiActivity: FiiDiiResponse;
  vixAnalysis: VixData;
  goldData: GoldData;
  silverData: SilverData;
  highLowData: HighLowData;
  heatmapAnalysis: string[];
  heatmapStocks: HeatmapStock[];
  giftNiftyData?: GiftNiftyData;
  realTimeOiData?: NiftyOiAnalysisData;
  marketVerdict?: { // Added
    verdict: string;
    details: string;
  };
}