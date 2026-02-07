import { StockInfo } from './types';

export interface NiftyMoversData {
  topGainers: StockInfo[];
  topLosers: StockInfo[];
}

const parseSection = (lines: string[], sectionTitle: string): StockInfo[] => {
  const stocks: StockInfo[] = [];
  const titleIndex = lines.findIndex(line => line.trim().startsWith(sectionTitle));

  if (titleIndex === -1) return [];

  // Data starts 3 lines after the title (skipping '====', the column headers, and '----')
  for (let i = titleIndex + 3; i < lines.length && stocks.length < 5; i++) {
    const line = lines[i].trim();

    if (line === '' || line.startsWith('=')) {
      break; // End of this section's data
    }

    const parts = line.split(/\s+/).filter(Boolean);
    if (parts.length === 3) {
      stocks.push({
        name: parts[0],
        value: parts[1], // Keep as string
        change: parts[2],
      });
    }
  }
  return stocks;
}


export const fetchAndParseNiftyMoversData = async (): Promise<NiftyMoversData> => {
  const response = await fetch('/Data/nifty50_movers.txt');
  if (!response.ok) {
    throw new Error(`Failed to fetch nifty movers data: ${response.statusText}`);
  }
  const text = await response.text();
  const lines = text.split('\n');

  const topGainers = parseSection(lines, 'Top 5 Gainers:');
  const topLosers = parseSection(lines, 'Top 5 Losers:');

  if (topGainers.length === 0 || topLosers.length === 0) {
    throw new Error('Failed to parse movers from nifty50_movers.txt');
  }

  return { topGainers, topLosers };
};