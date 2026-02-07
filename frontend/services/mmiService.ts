import Groq from "groq-sdk";
import { MmiData, NiftyChange } from './types';

export const fetchAndAnalyzeMmiData = async (): Promise<MmiData> => {
    // 1. Fetch text data from the local file.
    const response = await fetch('/Data/mmi.txt');
    if (!response.ok) {
        throw new Error('Failed to fetch mmi.txt');
    }
    const rawText = await response.text();

    // 2. Parse the text data with more robust logic.
    const lines = rawText.split('\n');
    let current: number | null = null;
    let previous: number | null = null;
    let niftyChange: NiftyChange | null = null;

    const niftyChangeRegex = /change in nifty\s*=\s*([+\-\d.]+)\s*\((.*?)\)/i;

    let zoneAnalysis: string | null = null;

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

        if (cleanedLine.startsWith('zone analysis:')) {
            zoneAnalysis = line.split('Zone Analysis:')[1].trim();
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

    // 3. Prepare the prompt for the Groq API.
    const prompt = `You will be given the weekly change for the Market Mood Index (MMI) and the NIFTY index.
---
MMI Change: From ${previous} to ${current}
NIFTY Change: ${niftyChange.value > 0 ? '+' : ''}${niftyChange.value} (${niftyChange.percentage})
Preferred Sentiment Analysis: "${zoneAnalysis || ''}"
---
Provide a two-point analysis based on this data.
1. Return the "Preferred Sentiment Analysis" sentence EXACTLY as provided above (if not empty). If empty, write a concise sentence about the change in market sentiment.
2. A concise sentence comparing the change in the MMI to the change in the NIFTY index.
   - IMPOTANT: If MMI indicates Greed (High) but NIFTY is negative, call it a **divergence** or **misalignment**, do NOT say the outlook is purely bullish.
   - If MMI indicates Fear (Low) but NIFTY is positive, call it a **cautious rally** or divergence.
   - Only call it "bullish" if BOTH MMI implies Greed/optimism AND Nifty is positive.

For the second point, highlight the most important keywords by enclosing them in double asterisks.
Ensure the first point also has the Zone name (e.g. Fear, Greed) bolded if strictly copying the preferred analysis (it might not be bolded yet, so add bolding to the Zone name if needed).

Return your response as a JSON object with a single key "analysis" which is an array of two strings.
Example: {"analysis": ["Market sentiment is in **Fear** zone 😰 (MMI: 40.50) (remains in Fear with slight improvement)", "The **pullback** in the MMI is **aligned** with the **negative** performance of the NIFTY index."]}
`;

    // 4. Call the Groq API with Error Handling.
    try {
        const groq = new Groq({ apiKey: process.env.GROQ_API_KEY, dangerouslyAllowBrowser: true });

        const completion = await groq.chat.completions.create({
            messages: [{ role: "user", content: prompt }],
            model: "llama-3.3-70b-versatile",
            temperature: 0.3, // Lower temp for strict adherence
            response_format: { type: "json_object" }
        });

        // 5. Parse the JSON response.
        const jsonStr = completion.choices[0]?.message?.content || "";

        const parsed = JSON.parse(jsonStr);
        if (parsed.analysis && Array.isArray(parsed.analysis) && parsed.analysis.length > 0) {

            // Fallback: If LLM ignored the instruction, force it if we have zoneAnalysis.
            // But we trust Llama-3.3 usually.

            return {
                current,
                previous,
                niftyChange,
                analysis: parsed.analysis
            };
        }
    } catch (e) {
        console.warn("Groq API failed for MMI (Rate Limit?), using fallback.", e);
        return {
            current,
            previous,
            niftyChange,
            analysis: [
                zoneAnalysis || `Market sentiment moved from **${previous}** to **${current}** (AI Unavailable).`,
                `Nifty change of **${niftyChange.value}** coincides with this shift.`
            ]
        };
    }

    return {
        current,
        previous,
        niftyChange,
        analysis: ["Analysis Unavailable.", "Refer to data."]
    };
};