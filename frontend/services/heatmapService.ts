import { HeatmapStock } from './types';

export const fetchAndGenerateHeatmapAnalysis = async (): Promise<{ analysis: string[], stocks: HeatmapStock[] }> => {
  try {
    const response = await fetch(`/Data/nifty50_heatmap.json?t=${new Date().getTime()}`);
    if (!response.ok) throw new Error("Failed to fetch heatmap data");

    // Parse JSON
    const stocks: HeatmapStock[] = await response.json();

    // Generate Analysis (Simple Rule-based)
    const advances = stocks.filter(s => s.change > 0).length;
    const declines = stocks.filter(s => s.change < 0).length;
    const unchanged = Math.max(0, 50 - advances - declines);

    // Sort to find top movers
    const sorted = [...stocks].sort((a, b) => b.change - a.change);
    const topGainer = sorted[0];
    const topLoser = sorted[sorted.length - 1];

    const marketSentiment = advances > declines ? "Bullish" : "Bearish";

    const overview = advances >= declines
      ? `**Heatmap Overview**: Green blocks dominate showing strength, with **${advances}** advancing stocks versus **${declines}** declining stocks, indicating overall bullish sentiment.`
      : `**Heatmap Overview**: Red blocks dominate showing weakness, with **${declines}** declining stocks versus **${advances}** advancing stocks, indicating overall bearish sentiment.`;

    const analysis = [
      `**Market Breadth**: **${advances}** Advances vs **${declines}** Declines indicating a ${marketSentiment} trend.`,
      `**Top Outperformer**: **${topGainer.symbol}** leading with **+${topGainer.change.toFixed(2)}%** gains.`,
      `**Top Laggard**: **${topLoser.symbol}** dragging with **${topLoser.change.toFixed(2)}%** loss.`,
      overview,
      `**Actionable Insight**: Focus on sectors with clustered Green blocks for momentum trades.`,
    ];

    return { analysis, stocks };
  } catch (error) {
    console.error("Heatmap Fetch Error:", error);
    return {
      analysis: [
        "**Data Unavailable**: Could not load Nifty 50 Heatmap data.",
        "Please check if the data source is updated.",
        "Visual heatmap will be empty."
      ],
      stocks: []
    };
  }
};