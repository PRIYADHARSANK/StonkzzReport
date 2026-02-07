import React from 'react';

interface MMIGaugeProps {
    value: number;
    date?: string;
}

const MMIGauge: React.FC<MMIGaugeProps> = ({ value, date }) => {
    // 0-100 scale map to -90 to 90 degrees
    // We want the gauge to be a semi-circle (180 deg).
    // Let's say zones:
    // 0-30: Ext Fear (Red)
    // 30-50: Fear (Yellow)
    // 50-70: Greed (Lime)
    // 70-100: Ext Greed (Green)

    // Normalize value to 0-100 range just in case
    const safeValue = Math.min(100, Math.max(0, value));

    // Calculate rotation: 0 -> -90deg, 100 -> 90deg
    const rotation = (safeValue / 100) * 180 - 90;

    return (
        <div className="w-full flex flex-col items-center">
            <svg viewBox="0 0 300 160" className="w-full max-w-md">
                {/* Zones Arcs */}
                {/* Red: 0-30 */}
                <path d="M 30 130 A 120 120 0 0 1 65.5 48.6" fill="none" stroke="#DC2626" strokeWidth="25" />
                {/* Yellow: 30-50 */}
                <path d="M 69.5 44.5 A 120 120 0 0 1 150 10" fill="none" stroke="#FBBF24" strokeWidth="25" />
                {/* Lime: 50-70 */}
                <path d="M 150 10 A 120 120 0 0 1 230.5 44.5" fill="none" stroke="#A3E635" strokeWidth="25" />
                {/* Green: 70-100 */}
                <path d="M 234.5 48.6 A 120 120 0 0 1 270 130" fill="none" stroke="#16A34A" strokeWidth="25" />

                {/* Tick Marks (Manual for clarity) */}
                <text x="35" y="155" fontSize="12" fontWeight="bold" fill="#333">0</text>
                <text x="60" y="35" fontSize="12" fontWeight="bold" fill="#333">30</text>
                <text x="142" y="30" fontSize="12" fontWeight="bold" fill="#333">50</text>
                <text x="235" y="35" fontSize="12" fontWeight="bold" fill="#333">70</text>
                <text x="255" y="155" fontSize="12" fontWeight="bold" fill="#333">100</text>

                {/* Zone Labels */}
                <text x="60" y="90" fontSize="10" fontWeight="bold" fill="#DC2626" transform="rotate(-45, 60, 90)">EXT FEAR</text>
                <text x="110" y="60" fontSize="10" fontWeight="bold" fill="#D97706" transform="rotate(-20, 110, 60)">FEAR</text>
                <text x="190" y="60" fontSize="10" fontWeight="bold" fill="#65A30D" transform="rotate(20, 190, 60)">GREED</text>
                <text x="240" y="90" fontSize="10" fontWeight="bold" fill="#16A34A" transform="rotate(45, 240, 90)">EXT GREED</text>


                {/* Needle */}
                <g transform={`translate(150, 130) rotate(${rotation})`}>
                    <path d="M -4 0 L 0 -110 L 4 0 Z" fill="#1E293B" />
                    <circle cx="0" cy="0" r="8" fill="#1E293B" />
                </g>

                {/* Value Text display */}
                <text x="150" y="155" textAnchor="middle" fontSize="20" fontWeight="bold" fill="#1E293B">
                    {safeValue.toFixed(2)}
                </text>
            </svg>
            <div className="mt-2 text-center">
                {date && <p className="text-xs text-slate-500 font-semibold">Updated: {date}</p>}
            </div>
        </div>
    );
};

export default MMIGauge;