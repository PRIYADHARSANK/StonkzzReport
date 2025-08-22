import { GoogleGenAI, GenerateContentResponse, Type } from "@google/genai";
import { MmiData, NiftyChange } from './types';

export const fetchAndAnalyzeMmiData = async (): Promise<MmiData> => {
    // 1. Fetch text data from the GitHub URL.
    const response = await fetch('https://raw.githubusercontent.com/Prasannapriyan/Generator/refs/heads/main/Data/mmi.txt');
    if (!response.ok) {
        throw new Error('Failed to fetch mmi.txt');
    }
    const rawText = await response.text();
    
    // 2. Parse the text data with more robust logic.
    const lines = rawText.split('\n');
    let current: number | null = null;
    let previous: number | null = null;
    let niftyChange: NiftyChange | null = null;

    const niftyChangeRegex = /change in nifty\s*=\s*([-\d.]+)\s*\((.*?)\)/i;

    for (const line of lines) {
        const cleanedLine = line.trim().toLowerCase();
        
        if (cleanedLine.startsWith('current mmi')) {
            const parts = cleanedLine.split('=');
            if (parts.length > 1) {
                current = parseFloat(parts[1].trim());
            }
        }
        
        if (cleanedLine.startsWith('change in mmi')) {
            const match = cleanedLine.match(/from\s+([\d.]+)/);
            if (match && match[1]) {
                previous = parseFloat(match[1]);
            }
        }
        
        const niftyMatch = cleanedLine.match(niftyChangeRegex);
        if (niftyMatch && niftyMatch.length === 3) {
            niftyChange = {
                value: parseFloat(niftyMatch[1]),
                percentage: niftyMatch[2]
            };
        }
    }

    if (current === null || previous === null || niftyChange === null || isNaN(current) || isNaN(previous) || isNaN(niftyChange.value)) {
        console.error("Failed to parse MMI data. Raw text:", `\n---\n${rawText}\n---`, "\nParsed values:", { current, previous, niftyChange });
        throw new Error('Failed to parse MMI and Nifty data from mmi.txt');
    }
    
    // 3. Prepare the prompt for the Gemini API.
    const prompt = `You will be given the weekly change for the Market Mood Index (MMI) and the NIFTY index.
---
MMI Change: From ${previous} to ${current}
NIFTY Change: ${niftyChange.value > 0 ? '+' : ''}${niftyChange.value} (${niftyChange.percentage})
---
Provide a two-point analysis based on this data.
1. A concise sentence about the change in market sentiment based on the MMI.
2. A concise sentence comparing the change in the MMI to the change in the NIFTY index, noting if they are aligned or diverging.

For both points, highlight the most important keywords (like 'Greed', 'Fear', 'bullish', 'bearish', 'aligned', 'diverged') by enclosing them in double asterisks.

Return your response as a JSON object with a single key "analysis" which is an array of two strings. The strings must contain the markdown for bolding.
Example: {"analysis": ["Market sentiment has **moderated** this week, moving from **Extreme Greed** to the **Greed** zone.", "The **pullback** in the MMI is **aligned** with the **negative** performance of the NIFTY index, suggesting a consistent **bearish** shift."]}
`;
    
    // 4. Call the Gemini API.
    const ai = new GoogleGenAI({ apiKey: process.env.API_KEY});
    const result: GenerateContentResponse = await ai.models.generateContent({
        model: 'gemini-2.5-flash',
        contents: prompt,
        config: {
            responseMimeType: "application/json",
            responseSchema: {
                type: Type.OBJECT,
                properties: {
                    analysis: {
                        type: Type.ARRAY,
                        items: {
                            type: Type.STRING
                        },
                        description: "An array of 2 strings analyzing the MMI and NIFTY change."
                    }
                }
            }
        }
    });

    // 5. Parse the JSON response from Gemini.
    let jsonStr = result.text.trim();
    const fenceRegex = /^```(\w*)?\s*\n?(.*?)\n?\s*```$/s;
    const match = jsonStr.match(fenceRegex);
    if (match && match[2]) {
      jsonStr = match[2].trim();
    }
    try {
      const parsed = JSON.parse(jsonStr);
      if (parsed.analysis && Array.isArray(parsed.analysis) && parsed.analysis.length > 0) {
        return {
            current,
            previous,
            niftyChange,
            analysis: parsed.analysis
        };
      }
    } catch (e) {
      console.error("Failed to parse Gemini response for MMI analysis:", e, "Raw response:", jsonStr);
    }

    throw new Error("Could not generate or parse MMI analysis from Gemini.");
};