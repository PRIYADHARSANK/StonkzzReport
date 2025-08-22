import { GoogleGenAI, GenerateContentResponse } from "@google/genai";
import { PcrData } from './types';

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
 * Fetches Nifty PCR data, sends it with a chart image to Gemini, and returns an AI-generated analysis.
 * @returns A promise that resolves to a PcrData object.
 */
export const fetchAndGeneratePcrAnalysis = async (): Promise<PcrData> => {
    // 1. Fetch and parse text data from the local file.
    const textResponse = await fetch('https://raw.githubusercontent.com/Prasannapriyan/Generator/refs/heads/main/Data/pcr.txt');
    if (!textResponse.ok) {
        throw new Error('Failed to fetch pcr.txt');
    }
    const rawText = await textResponse.text();
    
    const lines = rawText.split('\n');
    let pcr = '';
    let putOi = '';
    let callOi = '';

    const pcrLine = lines.find(l => l.includes('Current PCR'));
    if (pcrLine) {
        pcr = pcrLine.split(':')[1]?.trim() || '';
    }
    const putOiLine = lines.find(l => l.includes('Total Put OI'));
    if (putOiLine) {
        putOi = putOiLine.split(':')[1]?.trim() || '';
    }
    const callOiLine = lines.find(l => l.includes('Total Call OI'));
    if (callOiLine) {
        callOi = callOiLine.split(':')[1]?.trim() || '';
    }

    if (!pcr || !putOi || !callOi) {
        throw new Error('Could not parse raw data from pcr.txt');
    }
    
    const rawData = { pcr, putOi, callOi };

    // 2. Fetch the chart image and convert it to a Base64 Part for the API.
    const imageUrl = 'https://raw.githubusercontent.com/Prasannapriyan/Generator/refs/heads/main/Data/pcr.png';
    const imagePart = await urlToGoogleGenerativeAIPart(imageUrl, 'image/png');

    // 3. Prepare the text prompt for the Gemini API.
    const textPart = {
        text: `Analyze the provided NIFTY50 data. You have two distinct pieces of information:
1. A text file with the current, **total Put-Call Ratio (PCR)** data.
2. An image showing the trend of the **intraday PCR** throughout the trading day.

---
[TOTAL PCR DATA]
${rawText}
---

Based on BOTH the final current PCR value from the text and the intraday trend from the chart, provide a brief observation or analysis in a single sentence, between 20 and 30 words. Your analysis should mention both the overall sentiment (from the total PCR) and the intraday development (from the chart).

Highlight the most important keywords (like the total PCR value, 'bearish', 'bullish', 'intraday recovery') by enclosing them in double asterisks.

Example: "While the current PCR of **0.86** suggests overall **bearish** sentiment, the chart shows an **intraday recovery** from the day's lows, indicating late buying interest."`
    };
    
    // 4. Call the Gemini API.
    const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
    const response: GenerateContentResponse = await ai.models.generateContent({
        model: 'gemini-2.5-flash',
        contents: { parts: [imagePart, textPart] },
    });

    // 5. Parse and return the structured response.
    const summary = response.text;
    if (summary && summary.trim().length > 0) {
        return {
            rawData,
            summary: summary.trim()
        };
    }
    
    throw new Error("Could not generate PCR analysis from Gemini.");
};