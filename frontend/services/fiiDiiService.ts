import { FiiDiiResponse } from './types';

export const fetchAndParseFiiDiiData = async (): Promise<FiiDiiResponse> => {
  try {
    const response = await fetch('/Data/fii_dii_data.json');
    if (!response.ok) {
      // Fallback or retry? 
      throw new Error(`Failed to fetch FII/DII JSON: ${response.statusText}`);
    }
    const data: FiiDiiResponse = await response.json();
    return data;
  } catch (error) {
    console.error("Error fetching FII/DII data:", error);
    // Return empty structure to avoid crashing
    return {
      daily_data: [],
      summary: {
        last_7_days: { fii: 0, dii: 0 },
        last_10_days: { fii: 0, dii: 0 }
      }
    };
  }
};