import { KeyStocksPage3, KeyStockWatch } from './types';

export const fetchAndParseKeyStocksPage3Data = async (): Promise<KeyStocksPage3> => {
    const response = await fetch('https://raw.githubusercontent.com/Prasannapriyan/Generator/refs/heads/main/Data/key_stocks_to_watch.txt');
    if (!response.ok) {
        throw new Error(`Failed to fetch key stocks data: ${response.statusText}`);
    }
    const text = await response.text();
    const lines = text.split('\n').filter(line => line.trim() !== '');

    const allStocks: KeyStockWatch[] = [];
    const lineRegex = /^(.*?)\s*(\([+-][\d.]+%?\))/;

    for (const line of lines) {
        const match = line.match(lineRegex);
        if (match && match.length > 2) {
            const name = match[1].trim();
            const change = match[2].trim().replace(/[()]/g, '');
            allStocks.push({ name, change });
        }
    }

    const positive = allStocks.filter(s => s.change.startsWith('+')).slice(0, 5);
    const negative = allStocks.filter(s => s.change.startsWith('-')).slice(0, 5);

    return {
        positive,
        negative,
    };
};