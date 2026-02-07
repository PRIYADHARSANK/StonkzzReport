export interface GiftNiftyData {
    last_price: number;
    change: number;
    change_percent: number;
    open: number | null;
    high: number | null;
    low: number | null;
    prev_close: number | null;
    week_52_high: number | null;
    week_52_low: number | null;
    timestamp: string;
}

export const fetchGiftNiftyData = async (): Promise<GiftNiftyData | null> => {
    try {
        const response = await fetch('/Data/gift_nifty.json');
        if (!response.ok) {
            throw new Error(`Failed to fetch gift_nifty.json`);
        }
        const data: GiftNiftyData = await response.json();
        return data;
    } catch (error) {
        console.error("Error fetching GIFT Nifty data:", error);
        return null;
    }
};
