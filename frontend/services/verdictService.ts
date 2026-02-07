export interface MarketVerdict {
    verdict: string;
    details: string;
}

export const fetchAndParseMarketVerdict = async (): Promise<MarketVerdict> => {
    try {
        const response = await fetch('/Data/market_verdict.txt');
        if (!response.ok) {
            return { verdict: 'Unavailable', details: 'Could not fetch verdict.' };
        }
        const text = await response.text();
        const lines = text.split('\n');
        let verdict = '';
        let details = '';

        for (const line of lines) {
            if (line.startsWith('Verdict:')) {
                verdict = line.replace('Verdict:', '').trim();
            } else if (line.startsWith('Details:')) {
                details = line.replace('Details:', '').trim();
            }
        }

        return { verdict, details };
    } catch (error) {
        console.error("Error fetching verdict:", error);
        return { verdict: 'Error', details: 'Failed to load data.' };
    }
};
