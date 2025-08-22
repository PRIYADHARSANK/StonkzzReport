import { GoogleGenAI, GenerateContentResponse, Type } from "@google/genai";
import { ReportData } from './types';

/**
 * Converts an ArrayBuffer to a Base64 string in a browser-safe way.
 * @param buffer The ArrayBuffer to convert.
 * @returns The Base64 encoded string.
 */
function arrayBufferToBase64(buffer: ArrayBuffer): string {
  let binary = '';
  const bytes = new Uint8Array(buffer);
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}

/**
 * Fetches a resource from a URL and converts it into a GoogleGenerativeAI.Part object.
 * @param url The URL of the image to fetch.
 * @param mimeType The MIME type of the image.
 * @returns A promise that resolves to a Part object for the Gemini API.
 */
async function urlToGoogleGenerativeAIPart(url: string, mimeType: string) {
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`Failed to fetch image from ${url}: ${response.statusText}`);
    }
    const buffer = await response.arrayBuffer();
    const base64 = arrayBufferToBase64(buffer);
    return {
        inlineData: {
            mimeType,
            data: base64,
        },
    };
}

/**
 * Fetches Nifty OI data, sends it with a chart image to Gemini, and returns an AI-generated analysis.
 * @returns A promise that resolves to an array of three strings representing the analysis points.
 */
export const fetchAndGenerateNiftyOiAnalysis = async (): Promise<string[]> => {
    // 1. Fetch text data from the local file.
    const textResponse = await fetch('https://raw.githubusercontent.com/Prasannapriyan/Generator/refs/heads/main/Data/nifty_oi.txt');
    if (!textResponse.ok) {
        throw new Error('Failed to fetch nifty_oi.txt');
    }
    const rawText = await textResponse.text();

    // 2. Fetch the chart image and convert it to a Base64 Part for the API.
    const imageUrl = 'https://raw.githubusercontent.com/Prasannapriyan/Generator/refs/heads/main/Data/nifty_oi_chart.png';
    const imagePart = await urlToGoogleGenerativeAIPart(imageUrl, 'image/png');

    // 3. Prepare the text prompt for the Gemini API.
    const textPart = {
        text: `Based on the attached Nifty Open Interest chart image and the following data, provide a concise 3-point analysis.
---
${rawText}
---
In your analysis, highlight the most important keywords (like specific strike prices, support/resistance levels, or terms like 'Call OI' and 'Put OI') by enclosing them in double asterisks. For example: "Strong resistance is visible at the **25,500 CE** strike."

Return your response as a JSON object with a single key "summary" which is an array of 3 strings. The strings in the array should contain the markdown for bolding. For example: {"summary": ["Point 1 with a **highlighted** word.", "Point 2", "Point 3"]}`
    };
    
    // 4. Call the Gemini API.
    const ai = new GoogleGenAI({ apiKey: process.env.API_KEY});
    const response: GenerateContentResponse = await ai.models.generateContent({
        model: 'gemini-2.5-flash',
        contents: { parts: [imagePart, textPart] },
        config: {
            responseMimeType: "application/json",
            responseSchema: {
                type: Type.OBJECT,
                properties: {
                    summary: {
                        type: Type.ARRAY,
                        items: {
                            type: Type.STRING
                        },
                        description: "An array of 3 strings summarizing the Nifty OI analysis."
                    }
                }
            }
        }
    });

    // 5. Parse the JSON response from Gemini.
    let jsonStr = response.text.trim();
    const fenceRegex = /^```(\w*)?\s*\n?(.*?)\n?\s*```$/s;
    const match = jsonStr.match(fenceRegex);
    if (match && match[2]) {
      jsonStr = match[2].trim();
    }
    try {
      const parsed = JSON.parse(jsonStr);
      if (parsed.summary && Array.isArray(parsed.summary) && parsed.summary.length > 0) {
        return parsed.summary;
      }
    } catch (e) {
      console.error("Failed to parse Gemini response for Nifty OI:", e, "Raw response:", jsonStr);
    }
    
    // Throw an error if parsing fails or the response is not in the expected format.
    throw new Error("Could not generate or parse Nifty OI analysis from Gemini.");
};

type NiftyTechAnalysis = ReportData['niftyTechAnalysis'];

export const fetchAndGenerateNiftyTechAnalysis = async (): Promise<NiftyTechAnalysis> => {
    // 1. Fetch text data.
    const textResponse = await fetch('https://raw.githubusercontent.com/Prasannapriyan/Generator/refs/heads/main/Data/nifty_analysis.txt');
    if (!textResponse.ok) {
        throw new Error('Failed to fetch nifty_analysis.txt');
    }
    const rawText = await textResponse.text();

    // 2. Parse text data for resistance and support.
    const lines = rawText.split('\n');
    const resistance: string[] = [];
    const support: string[] = [];
    
    lines.forEach(line => {
        const parts = line.split(':').map(p => p.trim());
        if (parts.length === 2) {
            const key = parts[0];
            const value = parts[1];
            if (key.toLowerCase().startsWith('resistance')) {
                resistance.push(`${value} (${key})`);
            } else if (key.toLowerCase().startsWith('support')) {
                support.push(`${value} (${key})`);
            }
        }
    });

    if (resistance.length === 0 || support.length === 0) {
        throw new Error('Could not parse resistance/support from nifty_analysis.txt');
    }

    // 3. Fetch image.
    const imageUrl = 'https://raw.githubusercontent.com/Prasannapriyan/Generator/refs/heads/main/Data/nifty_chart.png';
    const imagePart = await urlToGoogleGenerativeAIPart(imageUrl, 'image/png');

    // 4. Prepare prompt for Gemini.
    const textPart = {
        text: `Analyze the provided Nifty 50 chart (last 5 days, 30-min candles) and data summary.
---
[DATA SUMMARY]
${rawText}
---
Based on the chart's price action, candlestick patterns, and the provided support/resistance levels, provide a two-point summary of the technical analysis. Each point should be a concise sentence. Highlight important keywords like price levels, patterns (e.g., 'consolidation', 'breakout'), or sentiment ('bullish', 'bearish') by enclosing them in double asterisks.

Return your response as a JSON object with a single key "analysis" which is an array of two strings. The strings must contain the markdown for bolding.
Example: {"analysis": ["Nifty is showing signs of **consolidation** near the **25,500** level after a recent uptrend.", "The price is holding above the short-term moving averages, suggesting underlying **bullish** momentum, but a breakout above **25,600** is needed for confirmation."]}
`
    };

    // 5. Call Gemini.
    const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
    const response: GenerateContentResponse = await ai.models.generateContent({
        model: 'gemini-2.5-flash',
        contents: { parts: [imagePart, textPart] },
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
                        description: "An array of 2 strings summarizing the Nifty technical analysis."
                    }
                }
            }
        }
    });

    // 6. Parse response and combine with parsed data.
    let jsonStr = response.text.trim();
    const fenceRegex = /^```(\w*)?\s*\n?(.*?)\n?\s*```$/s;
    const match = jsonStr.match(fenceRegex);
    if (match && match[2]) {
      jsonStr = match[2].trim();
    }
    
    try {
        const parsed = JSON.parse(jsonStr);
        if (parsed.analysis && Array.isArray(parsed.analysis) && parsed.analysis.length > 0) {
            return {
                analysis: parsed.analysis,
                resistance,
                support: support
            };
        }
    } catch (e) {
        console.error("Failed to parse Gemini response for Nifty Tech Analysis:", e, "Raw response:", jsonStr);
    }

    throw new Error("Could not generate or parse Nifty Tech Analysis from Gemini.");
};