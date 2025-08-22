import { HighLowData, HighLowStockInfo } from './types';

export const fetchAndParseHighLowData = async (): Promise<HighLowData> => {
    const response = await fetch('https://raw.githubusercontent.com/Prasannapriyan/Generator/refs/heads/main/Data/highlow.txt');
    if (!response.ok) {
        throw new Error(`Failed to fetch 52-week high/low data: ${response.statusText}`);
    }
    const text = await response.text();
    const lines = text.split('\n').map(line => line.trim()).filter(line => line);

    const highs: HighLowStockInfo[] = [];
    const lows: HighLowStockInfo[] = [];
    let currentSection: 'high' | 'low' | null = null;

    for (const line of lines) {
        if (line.includes('52 Week High')) {
            currentSection = 'high';
            continue;
        }
        if (line.includes('52 Week Low')) {
            currentSection = 'low';
            continue;
        }
        if (line.startsWith('=') || line.toLowerCase().startsWith('name - current price')) {
            continue;
        }

        const parts = line.split(' - ');
        if (parts.length === 4) {
            const stockInfo: HighLowStockInfo = {
                name: parts[0].trim(),
                price: parts[1].trim(),
                change: parts[2].trim(),
                value: parts[3].trim()
            };

            if (currentSection === 'high') {
                highs.push(stockInfo);
            } else if (currentSection === 'low') {
                lows.push(stockInfo);
            }
        }
    }

    if (highs.length === 0 && lows.length === 0) {
        throw new Error('Failed to parse any high/low data from highlow.txt');
    }

    return { highs, lows };
};