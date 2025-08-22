import React from 'react';

const MMIGauge: React.FC = () => {
    return (
        <div className="w-full flex justify-center">
            <img 
                src="https://raw.githubusercontent.com/Prasannapriyan/Generator/refs/heads/main/Data/mmi_gauge.png" 
                alt="Market Mood Index Gauge"
                className="w-full max-w-xl object-contain"
            />
        </div>
    );
};

export default MMIGauge;