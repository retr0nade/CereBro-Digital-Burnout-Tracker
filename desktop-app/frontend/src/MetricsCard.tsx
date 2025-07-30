import React from "react";

interface MetricsCardProps {
  title: string;
  value: string | number;
  description?: string;
}

export default function MetricsCard({ title, value, description }: MetricsCardProps) {
  return (
    <div className="bg-white rounded-xl shadow-md p-5 w-52 mx-2 flex flex-col items-start">
      <div className="text-xs tracking-wide uppercase font-bold text-gray-400 mb-1">
        {title}
      </div>
      <div className="text-2xl font-extrabold text-gray-900">{value}</div>
      {description && (
        <div className="text-xs text-gray-600 mt-1">{description}</div>
      )}
    </div>
  );
}
