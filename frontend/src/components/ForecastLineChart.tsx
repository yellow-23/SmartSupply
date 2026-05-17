import React from "react";
import {
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Line,
  ComposedChart
} from "recharts";

interface DataPoint {
  date: string;
  actual?: number;
  forecast?: number;
  lower?: number;
  upper?: number;
}

interface ForecastLineChartProps {
  data: DataPoint[];
  title?: string;
}

const ForecastLineChart = ({ data, title }: ForecastLineChartProps) => {
  return (
    <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 w-full h-full flex flex-col">
      {title && <h3 className="text-lg font-bold text-gray-800 mb-6">{title}</h3>}
      <div className="flex-1 w-full min-h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
            <XAxis 
              dataKey="date" 
              axisLine={false}
              tickLine={false}
              tick={{ fill: "#9CA3AF", fontSize: 12 }}
            />
            <YAxis 
              axisLine={false}
              tickLine={false}
              tick={{ fill: "#9CA3AF", fontSize: 12 }}
            />
            <Tooltip />
            <Legend verticalAlign="top" height={36} />
            
            <Line 
              type="monotone" 
              dataKey="actual" 
              stroke="#1F3864" 
              strokeWidth={3} 
              name="Venta Real"
            />
            <Line 
              type="monotone" 
              dataKey="forecast" 
              stroke="#2E75B6" 
              strokeWidth={3} 
              strokeDasharray="5 5"
              name="Predicción"
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default ForecastLineChart;
