import { FiiDiiData } from './types';

const parseNumber = (str: string): number => {
  // Removes commas and parses the string to a float.
  return parseFloat(str.replace(/,/g, ''));
};

export const fetchAndParseFiiDiiData = async (): Promise<FiiDiiData[]> => {
  const response = await fetch('https://raw.githubusercontent.com/Prasannapriyan/Generator/refs/heads/main/Data/fii_dii_data.txt');
  if (!response.ok) {
    throw new Error(`Failed to fetch FII/DII data: ${response.statusText}`);
  }
  const text = await response.text();
  const lines = text.split('\n');
  const fiiDiiData: FiiDiiData[] = [];

  const dataRegex = /(.+?)\s*:\s*FII\s*=\s*([-\d,.]+)\s*DII\s*=\s*([-\d,.]+)/;

  for (const line of lines) {
    const match = line.match(dataRegex);
    if (match) {
      const period = match[1].trim();
      const fii = parseNumber(match[2]);
      const dii = parseNumber(match[3]);
      
      if (!isNaN(fii) && !isNaN(dii)) {
          fiiDiiData.push({ period, fii, dii });
      }
    }
  }

  if (fiiDiiData.length === 0) {
    throw new Error('Failed to parse any FII/DII data from fii_dii_data.txt');
  }

  return fiiDiiData;
};