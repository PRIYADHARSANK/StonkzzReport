
import { SilverData, SilverHistoryEntry, SilverPrice } from './types';

const parseNumber = (str: string): number => {
  // Removes commas and other non-numeric characters except the decimal point
  return parseFloat(str.replace(/[^0-9.-]+/g,""));
};

export const fetchAndParseSilverData = async (): Promise<SilverData> => {
  const response = await fetch('https://raw.githubusercontent.com/Prasannapriyan/Generator/refs/heads/main/Data/silver_rates.txt');
  if (!response.ok) {
    throw new Error(`Failed to fetch silver rates data: ${response.statusText}`);
  }
  const text = await response.text();
  const lines = text.split('\n');

  let todayGram: SilverPrice | null = null;
  let todayKg: SilverPrice | null = null;
  const history: SilverHistoryEntry[] = [];

  const todayRateRegex = /₹\s*([\d,.]+)\s*\(Change:\s*₹\s*([\d,.]+)\s*(▲|▼)\)/;

  // --- Robust Parsing for Today's Rates ---
  const perGramLine = lines.find(l => l.trim().startsWith('Per Gram:'));
  if (perGramLine) {
    const matches = perGramLine.match(todayRateRegex);
    if (matches && matches.length >= 4) {
      const price = parseNumber(matches[1]);
      let change = parseNumber(matches[2]);
      if (matches[3] === '▼') {
        change = -change;
      }
      todayGram = { price, change };
    }
  }

  const perKgLine = lines.find(l => l.trim().startsWith('Per Kg:'));
  if (perKgLine) {
    const matches = perKgLine.match(todayRateRegex);
     if (matches && matches.length >= 4) {
      const price = parseNumber(matches[1]);
      let change = parseNumber(matches[2]);
      if (matches[3] === '▼') {
        change = -change;
      }
      todayKg = { price, change };
    }
  }

  // --- Robust Parsing for History Section ---
  const historyHeaderIndex = lines.findIndex(l => /Date\s*\|\s*1 gram/.test(l));
  if (historyHeaderIndex > -1) {
    for (let i = historyHeaderIndex + 2; i < lines.length; i++) {
        const line = lines[i].trim();
        if (line.startsWith('---') || line === '') break;

        const parts = line.split('|').map(p => p.trim());
        if (parts.length === 4) {
            const date = parts[0];
            const gramPart = parts[1];
            const price100g = parseNumber(parts[2]);
            const price1kg = parseNumber(parts[3]);
            
            const price1gMatch = gramPart.match(/₹\s*([\d,.]+)/);
            const change1gMatch = gramPart.match(/\((.*?)\)/);

            if (price1gMatch && change1gMatch) {
                const price1g = parseNumber(price1gMatch[1]);
                const change1g = parseNumber(change1gMatch[1]);
                history.push({ date, price1g, change1g, price100g, price1kg });
            }
        }
    }
  }

  if (!todayGram || !todayKg || history.length === 0) {
    console.error('Failed to parse silver data. Parsed values:', { todayGram, todayKg, history });
    throw new Error('Failed to parse silver data from file. The format might be incorrect.');
  }

  return { todayGram, todayKg, history: history.reverse() };
};
