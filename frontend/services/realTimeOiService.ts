export interface NiftyOiAnalysisData {
    summary: {
        spot: number;
        pcr: number;
        call_oi: number;
        put_oi: number;
        support: number;
        resistance: number;
        timestamp: string;
    };
    oi_chart_data: Array<{
        strike: number;
        call_oi: number;
        put_oi: number;
    }>;
    pcr_trend_data: Array<{
        time: string;
        pcr: number;
        spot: number;
    }>;
}

export const fetchRealTimeOiAnalysis = async (): Promise<NiftyOiAnalysisData | null> => {
    try {
        const response = await fetch('/Data/nifty_oi_analysis.json');
        if (!response.ok) {
            // Fallback or just throw
            throw new Error('Failed to fetch OI analysis');
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.warn("Real-time OI fetch failed:", error);
        return null;
    }
};
