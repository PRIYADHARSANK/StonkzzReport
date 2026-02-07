import Groq from "groq-sdk";
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
 * Fetches Nifty OI data and returns an AI-generated analysis based on text data.
 * @returns A promise that resolves to an array of three strings representing the analysis points.
 */
export const fetchAndGenerateNiftyOiAnalysis = async (): Promise<string[]> => {
    // 1. Fetch text data from the local file.
    const textResponse = await fetch('/Data/nifty_oi.txt');
    if (!textResponse.ok) {
        throw new Error('Failed to fetch nifty_oi.txt');
    }
    const rawText = await textResponse.text();

    // 2. Prepare prompt for Groq (Text Only).
    const prompt = `Based on the following Nifty Open Interest data, provide a concise 3-point analysis.
---
${rawText}
---
In your analysis, highlight the most important keywords (like specific strike prices, support/resistance levels, or terms like 'Call OI' and 'Put OI') by enclosing them in double asterisks. For example: "Strong resistance is visible at the **25,500 CE** strike."

Return your response as a JSON object with a single key "summary" which is an array of 3 strings. The strings in the array should contain the markdown for bolding. For example: {"summary": ["Point 1 with a **highlighted** word.", "Point 2", "Point 3"]}`;

    // 3. Call the Groq API (Text Only) with Error Handling.
    try {
        const groq = new Groq({ apiKey: process.env.GROQ_API_KEY, dangerouslyAllowBrowser: true });

        const completion = await groq.chat.completions.create({
            messages: [
                {
                    role: "user",
                    content: prompt
                }
            ],
            model: "llama-3.3-70b-versatile",
            temperature: 0.5,
            response_format: { type: "json_object" }
        });

        const jsonStr = completion.choices[0]?.message?.content || "";

        // 4. Parse the JSON response.
        const parsed = JSON.parse(jsonStr);
        if (parsed.summary && Array.isArray(parsed.summary) && parsed.summary.length > 0) {
            return parsed.summary;
        }
    } catch (e) {
        console.warn("Groq API failed (Rate Limit or other), failing back to static analysis.", e);
        // Fallback: Generate simple stat-based summary from raw text
        const summary: string[] = [];
        const lines = rawText.split('\n');

        const spotLine = lines.find(l => l.includes('Spot Price'));
        if (spotLine) summary.push(`Nifty is currently trading at **${spotLine.split(':')[1]?.trim() || 'Unknown'}**.`);

        const callOiLine = lines.find(l => l.includes('Total Call OI'));
        if (callOiLine) summary.push(`Overall sentiment shows **${callOiLine.trim()}** positions.`);

        summary.push("Detailed AI analysis is currently unavailable due to high traffic. Please refer to the table below.");
        return summary;
    }

    // Should not reach here if fallback works
    return ["Analysis Unavailable due to AI Rate Limit.", "Please check the data table directly.", "Retry later."];
};

type NiftyTechAnalysis = ReportData['niftyTechAnalysis'];

export const fetchAndGenerateNiftyTechAnalysis = async (): Promise<NiftyTechAnalysis> => {
    // 1. Fetch text data.
    const textResponse = await fetch('/Data/nifty_analysis.txt');
    if (!textResponse.ok) {
        throw new Error('Failed to fetch nifty_analysis.txt');
    }
    const rawText = await textResponse.text();

    // 2. Parse text data for resistance, support, and trend score.
    const lines = rawText.split('\n');
    const resistance: string[] = [];
    const support: string[] = [];
    let trendScore: number | undefined;

    lines.forEach(line => {
        const parts = line.split(':').map(p => p.trim());
        if (parts.length >= 2) {
            const key = parts[0];
            const value = parts[1];
            if (key.toLowerCase().startsWith('resistance')) {
                resistance.push(`${value} (${key})`);
            } else if (key.toLowerCase().startsWith('support')) {
                support.push(`${value} (${key})`);
            } else if (key === 'TrendScore') {
                const parsedScore = parseFloat(value);
                if (!isNaN(parsedScore)) {
                    trendScore = parsedScore;
                }
            }
        }
    });

    if (resistance.length === 0 || support.length === 0) {
        // Warning instead of error to allow partial data if file format changes
        console.warn('Could not parse all resistance/support from nifty_analysis.txt', rawText);
    }

    // 3. Prepare prompt for Groq (Text Only).
    const prompt = `Analyze the provided Nifty 50 technical data summary.
---
[DATA SUMMARY]
${rawText}
---
Based on the provided support/resistance levels, provide a two-point summary of the technical analysis. Each point should be a concise sentence. Highlight important keywords like price levels or sentiment ('bullish', 'bearish') by enclosing them in double asterisks.

Return your response as a JSON object with a single key "analysis" which is an array of two strings. The strings must contain the markdown for bolding.
Example: {"analysis": ["Nifty is showing signs of **consolidation** near the **25,500** level.", "The price is holding above support, suggesting underlying **bullish** momentum."]}`;

    // 4. Call Groq with Error Handling
    try {
        const groq = new Groq({ apiKey: process.env.GROQ_API_KEY, dangerouslyAllowBrowser: true });

        const completion = await groq.chat.completions.create({
            messages: [
                {
                    role: "user",
                    content: prompt
                }
            ],
            model: "llama-3.3-70b-versatile",
            temperature: 0.5,
            response_format: { type: "json_object" }
        });

        const jsonStr = completion.choices[0]?.message?.content || "";

        // 5. Parse response and combine with parsed data.
        const parsed = JSON.parse(jsonStr);
        if (parsed.analysis && Array.isArray(parsed.analysis) && parsed.analysis.length > 0) {
            return {
                analysis: parsed.analysis,
                resistance,
                support,
                trendScore
            };
        }
    } catch (e) {
        console.warn("Groq API failed for Tech Analysis, using fallback.", e);
        // Fallback
        return {
            analysis: [
                `Immediate resistance is observed at **${resistance[0]?.split(' ')[0] || 'Unknown'}**.`,
                `Critical support level is active at **${support[0]?.split(' ')[0] || 'Unknown'}**.`
            ],
            resistance,
            support,
            trendScore
        };
    }

    return {
        analysis: ["AI Analysis Unavailable.", "Please refer to levels below."],
        resistance,
        support,
        trendScore
    };
};