import { CurrencyData } from './types';

const currencyToFlag: { [key: string]: string } = {
  'USD': '🇺🇸',
  'JPY': '🇯🇵',
  'EUR': '🇪🇺',
  'SGD': '🇸🇬',
  'GBP': '🇬🇧',
  'AED': '🇦🇪',
};

export const fetchAndParseCurrencyData = async (): Promise<CurrencyData[]> => {
  const response = await fetch('/Data/currency_rates.txt');
  if (!response.ok) {
    throw new Error(`Failed to fetch currency rates data: ${response.statusText}`);
  }
  const text = await response.text();
  const lines = text.split('\n');
  const currencies: CurrencyData[] = [];

  const headerIndex = lines.findIndex(l => l.includes('Code') && l.includes('Country'));
  if (headerIndex === -1) {
    throw new Error('Could not find header in currency_rates.txt');
  }

  // Process lines after the header and separator
  for (let i = headerIndex + 2; i < lines.length; i++) {
    const line = lines[i];
    if (line.includes('---') || line.trim() === '') continue;

    const parts = line.split('|').map(p => p.trim());
    if (parts.length === 4) {
      const code = parts[0];
      const name = parts[1];
      const countryName = parts[2];
      // Clean the string to remove currency symbols and commas before parsing
      const value = parseFloat(parts[3].replace(/[^0-9.-]+/g, ""));

      if (!isNaN(value)) {
        currencies.push({
          code,
          name,
          countryName,
          value,
          countryFlag: currencyToFlag[code] || '🏳️',
        });
      }
    }
  }

  if (currencies.length === 0) {
    throw new Error('Failed to parse any currencies from currency_rates.txt');
  }

  return currencies;
};