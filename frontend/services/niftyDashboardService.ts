import { NiftyDashboardData } from './types';

// Helper to parse string values into numbers, cleaning currency/text artifacts.
const parseVal = (str: string | undefined): number => {
    if (!str) return 0;
    // Removes currency symbols, commas, and "Lakhs" text before parsing.
    return parseFloat(str.replace(/₹|,|Lakhs/gi, '').trim()) || 0;
};

// Helper to clean string values for display, removing currency symbols and commas.
const cleanStringVal = (str: string | undefined): string => {
    if (!str) return '0.00';
    return str.replace(/₹|,/gi, '').trim();
}

export const fetchAndParseNiftyDashboardData = async (): Promise<NiftyDashboardData> => {
    const response = await fetch(`/Data/nifty.txt?t=${new Date().getTime()}`);
    if (!response.ok) {
        throw new Error('Failed to fetch Nifty dashboard data');
    }
    const text = await response.text();
    const lines = text.split('\n');

    // A stateful parser that recognizes sections to handle duplicate keys like "High" and "Low".
    const data: { [key: string]: string } = {};
    let currentSection = '';

    for (const line of lines) {
        const trimmedLine = line.trim();
        // Skip empty lines or the main header
        if (!trimmedLine || trimmedLine.includes('DASHBOARD DATA')) {
            continue;
        }

        // Detect section headers and set the current context
        if (trimmedLine.endsWith('INFORMATION') || trimmedLine.endsWith('RANGE')) {
            // Create a unique prefix for keys in this section, e.g., "52-WEEK_RANGE"
            currentSection = trimmedLine.replace(/\s/g, '_');
            continue;
        }

        const parts = trimmedLine.split(':');
        if (parts.length > 1) {
            const key = parts[0].trim();
            const value = parts.slice(1).join(':').trim();

            // Prepend section prefix to keys that are not unique across sections.
            if (currentSection && (key === 'High' || key === 'Low')) {
                data[`${currentSection}_${key}`] = value;
            } else {
                data[key] = value;
            }
        }
    }

    // Robustly parse the 'Change' line: "Change: ₹+55.70 (+0.22%)"
    const changeLine = data['Change'] || '';
    const changeRegex = /₹([+-][\d,.]+)\s+\((.*?)\)/;
    const changeMatch = changeLine.match(changeRegex);

    const changeValueWithSign = changeMatch ? changeMatch[1] : '+0.00';
    const changePercent = changeMatch ? changeMatch[2] : '+0.00%';

    const isPositive = changeValueWithSign.startsWith('+');
    // The component expects the change value without a sign, as it adds the arrow itself
    const changeValue = changeValueWithSign.replace(/[+-]/, '');

    const currentValueNum = parseVal(data['Current Price']);

    return {
        name: 'NIFTY 50',
        currentValue: cleanStringVal(data['Current Price']),
        changeValue,
        changePercent,
        isPositive,
        prevClose: cleanStringVal(data['Previous Close']),
        open: cleanStringVal(data['Open']),
        volume: cleanStringVal(data['Volume']?.replace('Lakhs', '')), // cleanStringVal handles undefined
        week52: {
            low: parseVal(data['52-WEEK_RANGE_Low']),
            high: parseVal(data['52-WEEK_RANGE_High']),
            current: currentValueNum,
        },
        intraday: {
            low: parseVal(data['INTRADAY_RANGE_Low']),
            high: parseVal(data['INTRADAY_RANGE_High']),
            current: currentValueNum,
        }
    };
};