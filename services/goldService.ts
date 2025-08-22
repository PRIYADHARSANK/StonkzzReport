import { GoldData, GoldHistoryEntry, GoldPrice } from './types';

const parseNumber = (str: string): number => {
  // Removes commas and parses the string to a float.
  return parseFloat(str.replace(/,/g, ''));
};

export const fetchAndParseGoldData = async (): Promise<GoldData> => {
  const response = await fetch('https://raw.githubusercontent.com/Prasannapriyan/Generator/refs/heads/main/Data/gold_rates.txt');
  if (!response.ok) {
    throw new Error(`Failed to fetch gold rates data: ${response.statusText}`);
  }
  const text = await response.text();
  const lines = text.split('\n');

  let today24k: GoldPrice | null = null;
  let today22k: GoldPrice | null = null;
  const history: GoldHistoryEntry[] = [];

  const todayRateRegex = /:\s*₹\s*([\d,.]+)\s*\(Change:\s*₹\s*([\d,.]+)\s*(▲|▼)\)/;

  // --- Robust Parsing for Today's Rates ---
  const today24kLine = lines.find(l => l.trim().startsWith('24K Gold:'));
  if (today24kLine) {
    const matches = today24kLine.match(todayRateRegex);
    if (matches && matches.length >= 4) {
      const price = parseNumber(matches[1]);
      let change = parseNumber(matches[2]);
      if (matches[3] === '▼') {
        change = -change;
      }
      today24k = { price, change };
    }
  }

  const today22kLine = lines.find(l => l.trim().startsWith('22K Gold:'));
  if (today22kLine) {
    const matches = today22kLine.match(todayRateRegex);
     if (matches && matches.length >= 4) {
      const price = parseNumber(matches[1]);
      let change = parseNumber(matches[2]);
      if (matches[3] === '▼') {
        change = -change;
      }
      today22k = { price, change };
    }
  }


  // --- Robust Parsing for History Section ---
  const historyHeaderIndex = lines.findIndex(l => /Date\s*\|\s*24K Price/.test(l));
  if (historyHeaderIndex > -1) {
    for (let i = historyHeaderIndex + 2; i < lines.length; i++) {
      const line = lines[i].trim();
      if (line.startsWith('---') || line === '') break;

      const parts = line.split('|').map(p => p.trim());
      if (parts.length === 3) {
        const date = parts[0];

        const price24kMatch = parts[1].match(/₹\s*([\d,]+)/);
        const price24k = price24kMatch ? parseNumber(price24kMatch[1]) : null;
        const change24kMatch = parts[1].match(/\(([-]?\d+)\)/);
        const change24k = change24kMatch ? parseInt(change24kMatch[1], 10) : null;

        const price22kMatch = parts[2].match(/₹\s*([\d,]+)/);
        const price22k = price22kMatch ? parseNumber(price22kMatch[1]) : null;
        const change22kMatch = parts[2].match(/\(([-]?\d+)\)/);
        const change22k = change22kMatch ? parseInt(change22kMatch[1], 10) : null;

        if (date && price24k !== null && price22k !== null && change24k !== null && change22k !== null) {
          history.push({ date, price24k, price22k, change24k, change22k });
        }
      }
    }
  }

  if (!today24k || !today22k || history.length === 0) {
    console.error('Failed to parse gold data. Parsed values:', { today24k, today22k, history });
    throw new Error('Failed to parse gold data from file. The format might be incorrect.');
  }

  return { today24k, today22k, history: history.reverse() };
};