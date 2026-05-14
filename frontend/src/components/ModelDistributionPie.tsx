import React from 'react'; import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
const ModelDistributionPie = ({ data }) => {
  return (
    <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 h-full min-h-[300px]">
      <h3 className="text-lg font-bold text-gray-800 mb-6">Distribución de Modelos</h3>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie data={data} innerRadius={60} outerRadius={80} dataKey="value">
            {data.map((entry, index) => (
              <Cell key={index} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
};
export default ModelDistributionPie;
