'use client';

import { Card } from '@/components/ui/card';
import { LucideIcon } from 'lucide-react';
import { useEffect, useState } from 'react';

interface StatsCardProps {
  title: string;
  value: number;
  change?: string;
  trend?: 'up' | 'down';
  icon: LucideIcon;
  color: string;
  bgColor: string;
  withMiniChart?: boolean;
}

export function StatsCard({
  title,
  value,
  change,
  trend,
  icon: Icon,
  color,
  bgColor,
  withMiniChart = false,
}: StatsCardProps) {
  const [displayValue, setDisplayValue] = useState(0);

  // 숫자 카운터 애니메이션
  useEffect(() => {
    const duration = 1000; // 1초
    const steps = 50;
    const increment = value / steps;
    let current = 0;

    const timer = setInterval(() => {
      current += increment;
      if (current >= value) {
        current = value;
        clearInterval(timer);
      }
      setDisplayValue(Math.floor(current));
    }, duration / steps);

    return () => clearInterval(timer);
  }, [value]);

  return (
    <Card className="p-6 hover:shadow-lg transition-all duration-300 hover:-translate-y-1">
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <p className="text-sm font-medium text-muted-foreground">
            {title}
          </p>
          <div className="flex items-center gap-2">
            <p className="text-3xl font-bold text-foreground">
              {displayValue.toLocaleString()}
            </p>
            {change && (
              <span
                className={`text-xs font-medium px-2 py-1 rounded-full ${
                  trend === 'up'
                    ? 'bg-green-100 text-green-600'
                    : 'bg-red-100 text-red-600'
                }`}
              >
                {change}
              </span>
            )}
          </div>
          {withMiniChart && (
            <div className="h-8 w-full bg-gray-100 rounded mt-2">
              {/* 미니 차트 영역 - 나중에 구현 */}
              <div 
                className={`h-full ${bgColor} rounded transition-all duration-1000`}
                style={{ width: `${Math.min((displayValue / value) * 100, 100)}%` }}
              />
            </div>
          )}
        </div>
        <div className={`p-4 rounded-lg ${bgColor} transition-transform hover:scale-110`}>
          <Icon className={`h-8 w-8 ${color}`} />
        </div>
      </div>
    </Card>
  );
}