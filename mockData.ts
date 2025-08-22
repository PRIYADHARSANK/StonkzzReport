import { ReportData } from './services/types';

// The 'marketMood', 'goldData', 'silverData', 'globalIndices', 'globalCurrencies', 'fiiDiiActivity', 'niftyMovers', 'marketBulletin', 'keyStocksPage3', 'niftyOiAnalysis', 'niftyPcrAnalysis', 'vixAnalysis', 'niftyDashboardData', 'niftyTechAnalysis', 'highLowData', and 'heatmapAnalysis' properties are now fetched dynamically.
// This object provides the static base for the report.
export const initialReportData: Omit<ReportData, 'marketMood' | 'goldData' | 'silverData' | 'globalIndices' | 'globalCurrencies' | 'fiiDiiActivity' | 'niftyMovers' | 'marketBulletin' | 'keyStocksPage3' | 'niftyOiAnalysis' | 'niftyPcrAnalysis' | 'vixAnalysis' | 'niftyDashboardData' | 'niftyTechAnalysis' | 'highLowData' | 'heatmapAnalysis'> = {
  date: "Tue, 10 June 2025",
  sectorAnalysis: [
    { name: "NIFTY REALTY", change: "+9.35%" },
    { name: "NIFTY MIDCAP SELECT", change: "+4.64%" },
    { name: "NIFTY INDIA DIGITAL", change: "+3.35%" },
    { name: "NIFTY PSU BANK", change: "+3.33%" },
    { name: "NIFTY METAL", change: "+3.09%" },
  ],
   bankNiftyTechAnalysis: {
    daily: "Bank Nifty displayed bullish strength as it opened above the previous all-time high (ATH) of 56,695 and marked a new ATH around 57,049. However, it couldn't sustain the gains and faced selling pressure.",
    hourly: "It witnessed a gap-up and, consolidating in a tight range near the highs, the price is also comfortably above the 50 SMA, reinforcing short-term bullish strength. However, some profit booking is visible at the top.",
    resistance: ["56,900 – Immediate resistance zone", "57,000 – Psychological resistance area"],
    support: ["56,800 – Immediate Intraday support zone", "56,600 – Next support zone"],
  },
  stocksInFnoBan: ["Aditya Birla Fashion and Retail", "Chambal Fertilisers and Chemicals", "Hindustan Copper", "Titagarh Rail Systems"],
  stocksRemovedFromFnoBan: ["Manappuram Finance"],
};