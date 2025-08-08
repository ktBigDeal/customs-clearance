'use client';

import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useLanguage } from '@/contexts/LanguageContext';

const data = [
  { name: '1월', documents: 240, api: 420 },
  { name: '2월', documents: 380, api: 520 },
  { name: '3월', documents: 320, api: 480 },
  { name: '4월', documents: 450, api: 620 },
  { name: '5월', documents: 520, api: 580 },
  { name: '6월', documents: 480, api: 720 },
];

const englishData = [
  { name: 'Jan', documents: 240, api: 420 },
  { name: 'Feb', documents: 380, api: 520 },
  { name: 'Mar', documents: 320, api: 480 },
  { name: 'Apr', documents: 450, api: 620 },
  { name: 'May', documents: 520, api: 580 },
  { name: 'Jun', documents: 480, api: 720 },
];

export default function ChartSection() {
  const { t, language } = useLanguage();
  const chartData = language === 'ko' ? data : englishData;

  return (
    <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
      <h3 className="text-lg font-semibold text-slate-800 mb-6">
        {t('admin.monthlyProcessingChart')}
      </h3>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Area 
              type="monotone" 
              dataKey="documents" 
              stackId="1" 
              stroke="#3b82f6" 
              fill="#3b82f6" 
              fillOpacity={0.6}
              name={t('admin.documentProcessing')}
            />
            <Area 
              type="monotone" 
              dataKey="api" 
              stackId="2" 
              stroke="#06b6d4" 
              fill="#06b6d4" 
              fillOpacity={0.6}
              name={t('admin.apiCalls')}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}