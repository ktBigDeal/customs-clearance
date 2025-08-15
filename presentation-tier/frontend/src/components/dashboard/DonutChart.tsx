'use client';

import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';

interface DonutChartProps {
  data: Array<{
    status: string;
    count: number;
    label: string;
  }>;
}

// 상태별 색상 매핑
const STATUS_COLORS: { [key: string]: string } = {
  'PENDING_DOCUMENTS': '#f59e0b', // 주황색
  'UNDER_REVIEW': '#3b82f6',      // 파란색
  'APPROVED': '#10b981',          // 초록색
  'REJECTED': '#ef4444',          // 빨간색
  'CLEARED': '#059669',           // 진한 초록색
};

export function DonutChart({ data }: DonutChartProps) {
  // 데이터가 없을 때
  if (!data || data.length === 0) {
    return (
      <div className="h-64 w-full flex items-center justify-center text-muted-foreground">
        <div className="text-center">
          <div className="text-4xl mb-2">📊</div>
          <p>데이터가 없습니다</p>
        </div>
      </div>
    );
  }

  // 총합 계산
  const total = data.reduce((sum, item) => sum + item.count, 0);

  const renderCustomLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }: any) => {
    if (percent < 0.05) return null; // 5% 미만은 라벨 숨김
    
    const RADIAN = Math.PI / 180;
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);

    return (
      <text 
        x={x} 
        y={y} 
        fill="white" 
        textAnchor={x > cx ? 'start' : 'end'} 
        dominantBaseline="central"
        fontSize={12}
        fontWeight="bold"
      >
        {`${(percent * 100).toFixed(0)}%`}
      </text>
    );
  };

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={renderCustomLabel}
            outerRadius={80}
            innerRadius={40}
            fill="#8884d8"
            dataKey="count"
          >
            {data.map((entry, index) => (
              <Cell 
                key={`cell-${index}`} 
                fill={STATUS_COLORS[entry.status] || '#8884d8'}
              />
            ))}
          </Pie>
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const data = payload[0].payload;
                const percentage = ((data.count / total) * 100).toFixed(1);
                return (
                  <div className="rounded-lg border bg-background p-3 shadow-lg">
                    <div className="flex items-center gap-2">
                      <div 
                        className="w-3 h-3 rounded-full" 
                        style={{ backgroundColor: STATUS_COLORS[data.status] }}
                      />
                      <div>
                        <p className="font-medium">{data.label}</p>
                        <p className="text-sm text-muted-foreground">
                          {data.count}건 ({percentage}%)
                        </p>
                      </div>
                    </div>
                  </div>
                );
              }
              return null;
            }}
          />
          <Legend
            verticalAlign="bottom"
            height={36}
            formatter={(value, entry: any) => (
              <span className="text-sm font-medium" style={{ color: entry.color }}>
                {entry.payload.label} ({entry.payload.count}건)
              </span>
            )}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}