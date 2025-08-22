import { GoogleGenAI, GenerateContentResponse } from "@google/genai";
import { VixData } from './types';

/**
 * Converts an ArrayBuffer to a Base64 string in a browser-safe way.
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
 * Fetches a resource from a URL and converts it into a Part object for the Gemini API.
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
 * Fetches India VIX data, sends it with a chart image to Gemini, and returns an AI-generated analysis.
 */
export const fetchAndGenerateVixAnalysis = async (): Promise<VixData> => {
    // 1. Fetch and parse text data
    const textResponse = await fetch('https://raw.githubusercontent.com/Prasannapriyan/Generator/refs/heads/main/Data/vix.txt');
    if (!textResponse.ok) {
        throw new Error('Failed to fetch vix.txt');
    }
    const rawText = await textResponse.text();
    
    // Using more robust regex for parsing
    const valueMatch = rawText.match(/Current Value:\s*([\d.]+)/i);
    const changeMatch = rawText.match(/Change:\s*(.*)/i);

    const value = valueMatch ? valueMatch[1].trim() : '';
    const change = changeMatch ? changeMatch[1].trim() : '';

    if (!value || !change) {
        console.error("Parsing failed. Raw text:", rawText, "Matches:", {valueMatch, changeMatch});
        throw new Error('Could not parse raw data from vix.txt');
    }
    
    const rawData = { value, change };

    // 2. Fetch the chart image and convert it for the API
    const imageUrl = 'https://raw.githubusercontent.com/Prasannapriyan/Generator/refs/heads/main/Data/vix.png';
    const imagePart = await urlToGoogleGenerativeAIPart(imageUrl, 'image/png');

    // 3. Prepare the text prompt for the Gemini API
    const textPart = {
        text: `Analyze the provided India VIX data. You have two distinct pieces of information:
1. A text file with the current India VIX value and its change.
2. An image showing the intraday trend of the India VIX.

---
[VIX DATA]
${rawText}
---

Based on BOTH the final VIX value from the text and the intraday trend from the chart, provide a brief observation or analysis in a single sentence, between 20 and 30 words. Your analysis should mention the overall volatility level (e.g., 'low', 'high', 'moderate') and the intraday development (e.g., 'declined', 'spiked', 'remained stable').

Highlight the most important keywords (like the VIX value, 'low volatility', 'high complacency', 'declined sharply') by enclosing them in double asterisks.

Example: "The India VIX closed at **13.92**, indicating relatively **low volatility**, and the chart shows it **declined sharply** intraday, suggesting increasing market confidence."`
    };
    
    // 4. Call the Gemini API
    const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
    const response: GenerateContentResponse = await ai.models.generateContent({
        model: 'gemini-2.5-flash',
        contents: { parts: [imagePart, textPart] },
    });

    // 5. Parse and return the structured response
    const summary = response.text;
    if (summary && summary.trim().length > 0) {
        return {
            rawData,
            summary: summary.trim()
        };
    }
    
    throw new Error("Could not generate VIX analysis from Gemini.");
};