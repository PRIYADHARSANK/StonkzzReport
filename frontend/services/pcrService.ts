import Groq from "groq-sdk";
import { PcrData } from './types';

/**
 * Fetches Nifty PCR data and returns an AI-generated analysis based on text data.
 * @returns A promise that resolves to a PcrData object.
 */
export const fetchAndGeneratePcrAnalysis = async (): Promise<PcrData> => {
    // 1. Fetch and parse text data from the local file.
    const textResponse = await fetch('/Data/pcr.txt');
    if (!textResponse.ok) {
        throw new Error('Failed to fetch pcr.txt');
    }
    const rawText = await textResponse.text();

    const lines = rawText.split('\n');
    let pcr = '';
    let putOi = '';
    let callOi = '';
    let change = '';
    let changePct = '';

    const pcrLine = lines.find(l => l.includes('Current PCR'));
    if (pcrLine) {
        pcr = pcrLine.split(':')[1]?.trim() || '';
    }
    const changeLine = lines.find(l => l.includes('Change:'));
    if (changeLine) {
        change = changeLine.split(':')[1]?.trim() || '';
    }
    const changePctLine = lines.find(l => l.includes('Change %:'));
    if (changePctLine) {
        changePct = changePctLine.split(':')[1]?.trim() || '';
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

    const rawData = { pcr, putOi, callOi, change, changePct };

    // 2. Prepare the text prompt for the Groq API (Text Only).
    const prompt = `Analyze the provided NIFTY50 Put-Call Ratio (PCR) data.
---
[TOTAL PCR DATA]
${rawText}
---

Strict Interpretation Rules:
1. PCR > 1.05: **Bearish Lean / Defensive** (More Puts written suggests defensive hedging or bearish view).
2. 0.95 <= PCR <= 1.05: **Neutral / Balanced**.
3. PCR < 0.95: **Bullish** (Less Puts written relative to Calls).

Significant Change Rule:
- If the 'Change %' is greater than 15% (positive or negative), explicitly explicitly mention this as a **"Significant Shift"** in sentiment.

Based on the final current PCR value (${pcr}) and the rules above, provide a brief observation or analysis in a single sentence, between 20 and 30 words. Mention the overall sentiment accurately.

Highlight the most important keywords (like the total PCR value, sentiment label) by enclosing them in double asterisks.

Example: "The current PCR of **1.09** indicates a **Slight Bearish Lean**, suggesting defensive positioning by market participants."`;

    // 3. Call the Groq API with Error Handling.
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
            temperature: 0.2, // Lower temperature for more deterministic rule following
        });

        // 4. Parse and return the structured response.
        const summary = completion.choices[0]?.message?.content || "";
        if (summary && summary.trim().length > 0) {
            return {
                rawData,
                summary: summary.trim()
            };
        }
    } catch (e) {
        console.warn("Groq API failed for PCR (Rate Limit?), using fallback.", e);
        const pcrVal = parseFloat(pcr);
        let sentiment = "Neutral / Balanced";

        // Strict Fallback Logic
        if (pcrVal > 1.05) sentiment = "Bearish Lean / Defensive";
        else if (pcrVal < 0.95) sentiment = "Bullish";

        let changeNote = "";
        const chgPctVal = parseFloat(changePct.replace('%', ''));
        if (Math.abs(chgPctVal) > 15) {
            changeNote = ` noting a **Significant Shift** of ${changePct}`;
        }

        return {
            rawData,
            summary: `The current PCR of **${pcr}** indicates **${sentiment}** sentiment${changeNote} (AI Unavailable).`
        };
    }

    return {
        rawData,
        summary: "Analysis Unavailable."
    };
};