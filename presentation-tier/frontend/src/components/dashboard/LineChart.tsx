'use client';

import { LineChart as RechartsLineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface LineChartProps {
  data: Array<{
    month: string;
    count: number;
  }>;
}

export function LineChart({ data }: LineChartProps) {
  // 월 이름을 한국어로 변환
  const formatMonth = (month: string) => {
    const monthMap: { [key: string]: string } = {
      'JANUARY': '1월',
      'FEBRUARY': '2월',
      'MARCH': '3월',
      'APRIL': '4월',
      'MAY': '5월',
      'JUNE': '6월',
      'JULY': '7월',
      'AUGUST': '8월',
      'SEPTEMBER': '9월',
      'OCTOBER': '10월',
      'NOVEMBER': '11월',
      'DECEMBER': '12월',
    };
    return monthMap[month] || month;
  };

  const formattedData = data.map(item => ({
    ...item,
    month: formatMonth(item.month),
  }));

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <RechartsLineChart
          data={formattedData}
          margin={{
            top: 5,
            right: 30,
            left: 20,
            bottom: 5,
          }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis 
            dataKey="month" 
            stroke="#888888"
            fontSize={12}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            stroke="#888888"
            fontSize={12}
            tickLine={false}
            axisLine={false}
            tickFormatter={(value) => `${value}건`}
          />
          <Tooltip
            content={({ active, payload, label }) => {
              if (active && payload && payload.length) {
                return (
                  <div className="rounded-lg border bg-background p-2 shadow-lg">
                    <div className="grid grid-cols-2 gap-2">
                      <div className="flex flex-col">
                        <span className="text-[0.70rem] uppercase text-muted-foreground">
                          {label}
                        </span>
                        <span className="font-bold text-muted-foreground">
                          {payload[0].value}건
                        </span>
                      </div>
                    </div>
                  </div>
                );
              }
              return null;
            }}
          />
          <Line
            type="monotone"
            dataKey="count"
            strokeWidth={2}
            stroke="#2563eb"
            fill="#2563eb"
            dot={{ fill: '#2563eb', strokeWidth: 2, r: 4 }}
            activeDot={{ r: 6, stroke: '#2563eb', strokeWidth: 2 }}
          />
        </RechartsLineChart>
      </ResponsiveContainer>
    </div>
  );
}