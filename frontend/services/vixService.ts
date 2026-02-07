import Groq from "groq-sdk";
import { VixData } from './types';

/**
 * Fetches India VIX data and returns an AI-generated analysis based on text data.
 */
export const fetchAndGenerateVixAnalysis = async (): Promise<VixData> => {
    // 1. Fetch text data and history in parallel
    const [textResponse, historyResponse] = await Promise.all([
        fetch('/Data/vix.txt'),
        fetch('/Data/vix_history.json').catch(e => null) // Fallback if file missing
    ]);

    if (!textResponse.ok) {
        throw new Error('Failed to fetch vix.txt');
    }
    const rawText = await textResponse.text();

    // Parse History
    let history: any[] = [];
    if (historyResponse && historyResponse.ok) {
        try {
            history = await historyResponse.json();
        } catch (e) { console.error("Failed to parse VIX history", e); }
    }

    // Using more robust regex for parsing
    const valueMatch = rawText.match(/Current Value:\s*([\d.]+)/i);
    const changeMatch = rawText.match(/Change:\s*([-+\d.]+)/i); // Improved regex for negative/positive

    const value = valueMatch ? valueMatch[1].trim() : '';
    const change = changeMatch ? changeMatch[1].trim() : '';

    if (!value || !change) {
        console.error("Parsing failed. Raw text:", rawText, "Matches:", { valueMatch, changeMatch });
        throw new Error('Could not parse raw data from vix.txt');
    }

    const rawData = { value, change };

    // 2. Prepare the text prompt for the Groq API (Text Only)
    const prompt = `Analyze the provided India VIX data. current India VIX value: ${value}, change: ${change}.
---
[VIX DATA]
${rawText}
---

Based on the VIX value and the change, provide a brief observation or analysis in a single sentence, between 20 and 30 words. Mention the overall volatility level (e.g., 'low', 'high', 'moderate').

Highlight the most important keywords (like the VIX value, 'low volatility', 'high complacency') by enclosing them in double asterisks.

Example: "The India VIX closed at **13.92**, indicating relatively **low volatility**, suggesting increasing market confidence."`;

    // 3. Call the Groq API with Error Handling
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
        });

        // 4. Parse and return the structured response
        const summary = completion.choices[0]?.message?.content || "";
        if (summary && summary.trim().length > 0) {
            return {
                rawData,
                summary: summary.trim(),
                history
            };
        }
    } catch (e) {
        console.warn("Groq API failed for VIX (Rate Limit?), using fallback.", e);
        // Fallback
        const trend = parseFloat(change.replace(/[^\d.-]/g, '')) >= 0 ? "increased" : "decreased";
        const valNum = parseFloat(value);
        const level = valNum > 20 ? "high" : (valNum > 15 ? "moderate" : "low");
        return {
            rawData,
            summary: `The India VIX is at **${value}** (${trend}), indicating **${level} volatility** in the market (AI Unavailable).`,
            history
        };
    }

    // Should not reach here if fallback works
    return {
        rawData,
        summary: "Analysis Unavailable.",
        history
    };
};