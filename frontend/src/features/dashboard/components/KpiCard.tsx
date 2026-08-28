import { TrendingUp, TrendingDown } from "lucide-react";
import { cn } from "../../../shared/lib/utils";

interface KpiCardProps {
  label: string;
  value: string;
  icon: React.ReactNode;
  trend?: {
    value: string;
    direction: "up" | "down";
    isGood: boolean;
  };
  valueClassName?: string;
}

export function KpiCard({ label, value, icon, trend, valueClassName }: KpiCardProps) {
  const trendGood = trend && trend.isGood;
  const trendBad = trend && !trend.isGood;

  return (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-gray-400 uppercase tracking-widest">{label}</span>
        <div
          className="w-8 h-8 rounded-lg bg-blue-900 flex items-center justify-center text-white [&>svg]:w-4 [&>svg]:h-4"
        >
          {icon}
        </div>
      </div>
      <div className={cn("text-3xl font-bold tracking-tight text-gray-900", valueClassName)}>
        {value}
      </div>
      {trend && (
        <div className={cn(
          "flex items-center gap-1 text-sm font-medium",
          trendGood ? "text-green-600" : "text-red-600"
        )}>
          {trend.direction === "up"
            ? <TrendingUp className="w-4 h-4" />
            : <TrendingDown className="w-4 h-4" />
          }
          {trend.value}
        </div>
      )}
    </div>
  );
}
