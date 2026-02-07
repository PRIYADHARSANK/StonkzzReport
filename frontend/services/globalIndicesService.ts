import { IndexData } from './types';

const indexToCountryFlag: { [key: string]: string } = {
  'Dow Jones': '🇺🇸',
  'Nasdaq': '🇺🇸',
  'S&P 500': '🇺🇸',
  'Hang Seng': '🇭🇰',
  'FTSE 100': '🇬🇧',
};


export const fetchAndParseGlobalIndicesData = async (): Promise<IndexData[]> => {
  const response = await fetch('/Data/global_markets.txt');
  if (!response.ok) {
    throw new Error(`Failed to fetch global indices data: ${response.statusText}`);
  }
  const text = await response.text();
  const lines = text.split('\n');
  const indices: IndexData[] = [];

  const headerIndex = lines.findIndex(l => l.includes('Name') && (l.includes('LTP') || l.includes('Close')));
  if (headerIndex === -1) {
    throw new Error('Could not find header in global_markets.txt');
  }

  // Start processing lines after the header and separator
  for (let i = headerIndex + 2; i < lines.length; i++) {
    const line = lines[i];
    // Stop at the end of the table
    if (line.includes('---') || line.trim() === '') continue;

    const parts = line.split('|').map(p => p.trim());
    if (parts.length === 4) {
      const name = parts[0];
      indices.push({
        name: name,
        country: indexToCountryFlag[name] || '🏳️',
        ltp: parts[1],
        change: parts[2],
        changePercent: parts[3],
      });
    }
  }

  if (indices.length === 0) {
    throw new Error('Failed to parse any indices from global_markets.txt');
  }

  return indices;
};