import React from "react";

interface KPICardProps {
  title: string;
  value: string;
  trend?: string;
  subtext?: string;
  icon: React.ReactNode;
  color: string;
}

const KPICard: React.FC<KPICardProps> = ({ title, value, trend, subtext, icon, color }) => {
  const isNegativeTrend = trend?.startsWith("-");
  
  return (
    <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex items-start justify-between">
      <div className="flex-1">
        <p className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">{title}</p>
        <h3 className={"text-2xl font-black " + color}>{value}</h3>
        {trend && (
          <div className="flex items-center mt-3 space-x-1">
            <span className={"text-xs font-bold " + (isNegativeTrend ? "text-green-500" : "text-red-500")}>
              {trend}
            </span>
            <span className="text-[10px] text-gray-400 font-medium italic">vs mes anterior</span>
          </div>
        )}
        {subtext && <p className="text-[10px] mt-2 text-gray-400 font-medium">{subtext}</p>}
      </div>
      <div className={"p-3 rounded-xl bg-gray-50 " + color}>{icon}</div>
    </div>
  );
};

export default KPICard;
