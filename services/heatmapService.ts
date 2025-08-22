import { GoogleGenAI, GenerateContentResponse, Type } from "@google/genai";

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
 * Fetches the NIFTY50 heatmap, sends it to Gemini, and returns an AI-generated 8-point analysis.
 * @returns A promise that resolves to an array of 8 strings representing the analysis points.
 */
export const fetchAndGenerateHeatmapAnalysis = async (): Promise<string[]> => {
    // 1. Fetch the heatmap image and convert it for the API.
    const imageUrl = 'https://raw.githubusercontent.com/Prasannapriyan/Generator/refs/heads/main/Data/heatmap.png';
    const imagePart = await urlToGoogleGenerativeAIPart(imageUrl, 'image/png');

    // 2. Prepare the text prompt for the Gemini API.
    const textPart = {
        text: `Analyze the provided NIFTY50 heatmap. Based *only* on the visual information in the image (colors, box sizes, stock names, and sector groupings), provide a concise 8-point analysis.
        
Your analysis should cover:
- The overall market sentiment (e.g., bullish, bearish, mixed).
- The best performing sector and a key stock within it.
- The worst performing sector and a key stock within it.
- Mention specific heavyweight stocks (like Reliance, HDFC Bank, ICICI Bank) and their performance.
- Comment on the performance of the IT sector.
- Comment on the performance of another major sector (e.g., Financial Services, Oil & Gas).
- Identify any outlier stocks that are performing against their sector's trend.
- A concluding summary sentence.

Highlight important keywords (like sector names, stock names, or sentiment) by enclosing them in double asterisks. For example: "The **Financial Services** sector appears to be the main driver of the gains."

Return your response as a JSON object with a single key "analysis" which is an array of 8 strings. The strings must contain the markdown for bolding.
Example: {"analysis": ["Overall market sentiment is **positive**.", "Point 2...", "Point 3...", "Point 4...", "Point 5...", "Point 6...", "Point 7...", "Point 8..."]}`
    };
    
    // 3. Call the Gemini API.
    const ai = new GoogleGenAI({ apiKey: process.env.API_KEY});
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
                        description: "An array of 8 strings providing analysis of the heatmap."
                    }
                }
            }
        }
    });

    // 4. Parse the JSON response from Gemini.
    let jsonStr = response.text.trim();
    const fenceRegex = /^```(\w*)?\s*\n?(.*?)\n?\s*```$/s;
    const match = jsonStr.match(fenceRegex);
    if (match && match[2]) {
      jsonStr = match[2].trim();
    }
    try {
      const parsed = JSON.parse(jsonStr);
      if (parsed.analysis && Array.isArray(parsed.analysis) && parsed.analysis.length === 8) {
        return parsed.analysis;
      }
    } catch (e) {
      console.error("Failed to parse Gemini response for Heatmap Analysis:", e, "Raw response:", jsonStr);
    }
    
    // Throw an error if parsing fails or the response is not in the expected format.
    throw new Error("Could not generate or parse Heatmap analysis from Gemini. The response format was incorrect.");
};