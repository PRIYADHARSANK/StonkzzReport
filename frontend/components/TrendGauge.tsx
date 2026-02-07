import React from 'react';

interface TrendGaugeProps {
    score: number; // 0 to 100
    label?: string;
}

const TrendGauge: React.FC<TrendGaugeProps> = ({ score, label = "Trend Strength" }) => {
    // Determine color and text based on score
    let color = 'text-yellow-500';
    let text = 'Neutral';
    let gaugeColor = '#EAB308'; // yellow-500

    if (score >= 80) {
        color = 'text-green-600';
        text = 'Strong Buy';
        gaugeColor = '#16A34A';
    } else if (score >= 60) {
        color = 'text-green-500';
        text = 'Buy';
        gaugeColor = '#22C55E';
    } else if (score <= 20) {
        color = 'text-red-600';
        text = 'Strong Sell';
        gaugeColor = '#DC2626';
    } else if (score <= 40) {
        color = 'text-red-500';
        text = 'Sell';
        gaugeColor = '#EF4444';
    }

    // Rotation for needle: 0 to 180 degrees.
    // score 0 -> -90deg, 50 -> 0deg, 100 -> 90deg ? No, let's map 0-100 to 0-180 for a semi-circle.
    const rotation = (score / 100) * 180;

    return (
        <div className="flex flex-col items-center justify-center p-4 bg-white/50 rounded-xl border border-brand-black/20 shadow-sm">
            <h3 className="text-lg font-bold font-heading mb-2">{label}</h3>

            {/* Gauge Container */}
            <div className="relative w-48 h-24 overflow-hidden mb-2">
                {/* Background Arc */}
                <div className="absolute top-0 left-0 w-48 h-48 rounded-full border-[20px] border-slate-200 box-border"></div>

                {/* Colored Arc - simplified as zones or just gradient? Gradient is nice */}
                <div
                    className="absolute top-0 left-0 w-48 h-48 rounded-full border-[20px] border-transparent box-border"
                    style={{
                        background: `conic-gradient(from 180deg, #EF4444 0deg, #F59E0B 90deg, #22C55E 180deg)`,
                        maskImage: 'radial-gradient(transparent 55%, black 56%)',
                        WebkitMaskImage: 'radial-gradient(transparent 55%, black 56%)'
                    }}
                ></div>

                {/* Needle */}
                <div
                    className="absolute bottom-0 left-1/2 w-1 h-24 bg-brand-black origin-bottom transform transition-transform duration-1000 ease-out"
                    style={{ transform: `translateX(-50%) rotate(${rotation - 90}deg)` }}
                >
                    <div className="absolute -top-1 -left-1.5 w-4 h-4 rounded-full bg-brand-black"></div>
                </div>
            </div>

            {/* Value Text */}
            <div className="text-center mt-[-10px] z-10">
                <div className="text-2xl font-bold font-mono">{score}</div>
                <div className={`text-sm font-bold uppercase ${color}`}>{text}</div>
            </div>
        </div>
    );
};

export default TrendGauge;
