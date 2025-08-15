'use client';

import { useEffect, useState } from 'react';
import { TrendingUp, Clock, CheckCircle } from 'lucide-react';

interface HeroSectionProps {
  todayProcessed?: number;
  totalDeclarations?: number;
  processingTime?: number;
}

export function CustomsHeroSection({ 
  todayProcessed = 0, 
  totalDeclarations = 0,
  processingTime = 0 
}: HeroSectionProps) {
  const [animatedToday, setAnimatedToday] = useState(0);
  const [currentTime, setCurrentTime] = useState(new Date());

  // 오늘 처리 건수 애니메이션
  useEffect(() => {
    const duration = 2000; // 2초
    const steps = 60;
    const increment = todayProcessed / steps;
    let current = 0;

    const timer = setInterval(() => {
      current += increment;
      if (current >= todayProcessed) {
        current = todayProcessed;
        clearInterval(timer);
      }
      setAnimatedToday(Math.floor(current));
    }, duration / steps);

    return () => clearInterval(timer);
  }, [todayProcessed]);

  // 실시간 시계
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const formatTime = (date: Date) => {
    return new Intl.DateTimeFormat('ko-KR', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    }).format(date);
  };

  const formatDate = (date: Date) => {
    return new Intl.DateTimeFormat('ko-KR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      weekday: 'long',
    }).format(date);
  };

  return (
    <div className="relative overflow-hidden bg-gradient-to-r from-blue-600 via-blue-700 to-blue-800 text-white p-8 rounded-lg shadow-lg">
      {/* 배경 패턴 */}
      <div className="absolute inset-0 opacity-10">
        <div className="absolute top-0 left-0 w-full h-full bg-repeat opacity-20"
             style={{
               backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.1'%3E%3Ccircle cx='7' cy='7' r='7'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
             }}
        />
      </div>

      <div className="relative z-10">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
          {/* 왼쪽: 메인 텍스트 */}
          <div className="space-y-4">
            <div>
              <h1 className="text-3xl lg:text-4xl font-bold mb-2">
                통관 현황 대시보드
              </h1>
              <p className="text-blue-100 text-lg">
                실시간 통관 데이터 기반 관리 시스템
              </p>
            </div>
            
            <div className="flex items-center gap-6">
              <div className="flex items-center gap-2">
                <Clock className="h-5 w-5 text-blue-200" />
                <div>
                  <div className="text-sm text-blue-200">현재 시각</div>
                  <div className="font-mono text-lg font-bold">
                    {formatTime(currentTime)}
                  </div>
                </div>
              </div>
              
              <div className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-blue-200" />
                <div>
                  <div className="text-sm text-blue-200">평균 처리시간</div>
                  <div className="font-bold">
                    {processingTime > 0 ? `${processingTime}일` : '계산 중...'}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* 오른쪽: 오늘 통계 */}
          <div className="text-center lg:text-right">
            <div className="bg-white/10 backdrop-blur-sm rounded-lg p-6 border border-white/20">
              <div className="flex items-center justify-center lg:justify-end gap-2 mb-2">
                <CheckCircle className="h-6 w-6 text-green-300" />
                <span className="text-sm text-blue-100">오늘 처리 완료</span>
              </div>
              <div className="text-4xl lg:text-5xl font-bold mb-1">
                {animatedToday.toLocaleString()}
              </div>
              <div className="text-lg text-blue-100">건</div>
              
              {totalDeclarations > 0 && (
                <div className="mt-3 pt-3 border-t border-white/20">
                  <div className="text-sm text-blue-200">
                    전체 신고서: {totalDeclarations.toLocaleString()}건
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* 하단: 날짜 및 상태 */}
        <div className="mt-6 pt-6 border-t border-white/20">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
            <div className="text-blue-100">
              {formatDate(currentTime)}
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
              <span className="text-sm text-blue-100">시스템 정상 운영 중</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}