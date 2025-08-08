'use client';

import { useState } from 'react';
import { Save, RefreshCw, Shield, Database, Bell, Mail, Globe, Server, Key, Users } from 'lucide-react';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { useLanguage } from '@/contexts/LanguageContext';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

interface SystemSettings {
  general: {
    systemName: string;
    systemVersion: string;
    maintenanceMode: boolean;
    debugMode: boolean;
  };
  security: {
    passwordMinLength: number;
    sessionTimeout: number;
    maxLoginAttempts: number;
    twoFactorAuth: boolean;
  };
  database: {
    backupInterval: string;
    retentionPeriod: number;
    autoOptimize: boolean;
  };
  notifications: {
    emailEnabled: boolean;
    smsEnabled: boolean;
    systemAlerts: boolean;
    userNotifications: boolean;
  };
  api: {
    rateLimit: number;
    apiVersion: string;
    logLevel: string;
  };
}

export default function SettingsPage() {
  const { t } = useLanguage();
  const [settings, setSettings] = useState<SystemSettings>({
    general: {
      systemName: '관세청 통관시스템',
      systemVersion: '2.1.0',
      maintenanceMode: false,
      debugMode: false,
    },
    security: {
      passwordMinLength: 8,
      sessionTimeout: 120,
      maxLoginAttempts: 5,
      twoFactorAuth: true,
    },
    database: {
      backupInterval: 'daily',
      retentionPeriod: 90,
      autoOptimize: true,
    },
    notifications: {
      emailEnabled: true,
      smsEnabled: false,
      systemAlerts: true,
      userNotifications: true,
    },
    api: {
      rateLimit: 1000,
      apiVersion: 'v1',
      logLevel: 'info',
    }
  });
  
  const [isSaving, setIsSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  const updateSetting = (section: keyof SystemSettings, key: string, value: any) => {
    setSettings(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [key]: value
      }
    }));
    setHasChanges(true);
  };

  const handleSave = async () => {
    setIsSaving(true);
    // 시뮬레이션 지연
    await new Promise(resolve => setTimeout(resolve, 1500));
    setIsSaving(false);
    setHasChanges(false);
    // TODO: API 호출로 설정 저장
  };

  const handleReset = () => {
    // 기본값으로 리셋
    setSettings({
      general: {
        systemName: '관세청 통관시스템',
        systemVersion: '2.1.0',
        maintenanceMode: false,
        debugMode: false,
      },
      security: {
        passwordMinLength: 8,
        sessionTimeout: 120,
        maxLoginAttempts: 5,
        twoFactorAuth: true,
      },
      database: {
        backupInterval: 'daily',
        retentionPeriod: 90,
        autoOptimize: true,
      },
      notifications: {
        emailEnabled: true,
        smsEnabled: false,
        systemAlerts: true,
        userNotifications: true,
      },
      api: {
        rateLimit: 1000,
        apiVersion: 'v1',
        logLevel: 'info',
      }
    });
    setHasChanges(false);
  };

  return (
    <ProtectedRoute requiredRole="admin">
      <DashboardLayout isAdmin={true}>
        <div className="space-y-6">
          {/* Page Header */}
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
              <h1 className="text-2xl font-bold text-foreground">
                시스템 설정
              </h1>
              <p className="text-muted-foreground">
                시스템 전반적인 설정을 관리하세요
              </p>
            </div>
            <div className="flex gap-2">
              <Button 
                variant="outline" 
                onClick={handleReset}
                disabled={isSaving}
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                초기화
              </Button>
              <Button 
                onClick={handleSave}
                disabled={isSaving || !hasChanges}
              >
                {isSaving ? (
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    <span>저장 중...</span>
                  </div>
                ) : (
                  <>
                    <Save className="w-4 h-4 mr-2" />
                    설정 저장
                  </>
                )}
              </Button>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* General Settings */}
            <Card className="p-6">
              <div className="flex items-center gap-2 mb-4">
                <Globe className="w-5 h-5 text-blue-600" />
                <h2 className="text-lg font-semibold">일반 설정</h2>
              </div>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    시스템 이름
                  </label>
                  <input
                    type="text"
                    value={settings.general.systemName}
                    onChange={(e) => updateSetting('general', 'systemName', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    시스템 버전
                  </label>
                  <input
                    type="text"
                    value={settings.general.systemVersion}
                    onChange={(e) => updateSetting('general', 'systemVersion', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium text-gray-700">
                    유지보수 모드
                  </label>
                  <input
                    type="checkbox"
                    checked={settings.general.maintenanceMode}
                    onChange={(e) => updateSetting('general', 'maintenanceMode', e.target.checked)}
                    className="w-4 h-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                </div>
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium text-gray-700">
                    디버그 모드
                  </label>
                  <input
                    type="checkbox"
                    checked={settings.general.debugMode}
                    onChange={(e) => updateSetting('general', 'debugMode', e.target.checked)}
                    className="w-4 h-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                </div>
              </div>
            </Card>

            {/* Security Settings */}
            <Card className="p-6">
              <div className="flex items-center gap-2 mb-4">
                <Shield className="w-5 h-5 text-red-600" />
                <h2 className="text-lg font-semibold">보안 설정</h2>
              </div>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    최소 비밀번호 길이
                  </label>
                  <input
                    type="number"
                    value={settings.security.passwordMinLength}
                    onChange={(e) => updateSetting('security', 'passwordMinLength', parseInt(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    min="6"
                    max="20"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    세션 타임아웃 (분)
                  </label>
                  <input
                    type="number"
                    value={settings.security.sessionTimeout}
                    onChange={(e) => updateSetting('security', 'sessionTimeout', parseInt(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    min="30"
                    max="480"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    최대 로그인 시도 횟수
                  </label>
                  <input
                    type="number"
                    value={settings.security.maxLoginAttempts}
                    onChange={(e) => updateSetting('security', 'maxLoginAttempts', parseInt(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    min="3"
                    max="10"
                  />
                </div>
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium text-gray-700">
                    2단계 인증
                  </label>
                  <input
                    type="checkbox"
                    checked={settings.security.twoFactorAuth}
                    onChange={(e) => updateSetting('security', 'twoFactorAuth', e.target.checked)}
                    className="w-4 h-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                </div>
              </div>
            </Card>

            {/* Database Settings */}
            <Card className="p-6">
              <div className="flex items-center gap-2 mb-4">
                <Database className="w-5 h-5 text-green-600" />
                <h2 className="text-lg font-semibold">데이터베이스 설정</h2>
              </div>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    백업 주기
                  </label>
                  <select
                    value={settings.database.backupInterval}
                    onChange={(e) => updateSetting('database', 'backupInterval', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="hourly">매시간</option>
                    <option value="daily">매일</option>
                    <option value="weekly">매주</option>
                    <option value="monthly">매월</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    데이터 보관 기간 (일)
                  </label>
                  <input
                    type="number"
                    value={settings.database.retentionPeriod}
                    onChange={(e) => updateSetting('database', 'retentionPeriod', parseInt(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    min="30"
                    max="365"
                  />
                </div>
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium text-gray-700">
                    자동 최적화
                  </label>
                  <input
                    type="checkbox"
                    checked={settings.database.autoOptimize}
                    onChange={(e) => updateSetting('database', 'autoOptimize', e.target.checked)}
                    className="w-4 h-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                </div>
              </div>
            </Card>

            {/* Notification Settings */}
            <Card className="p-6">
              <div className="flex items-center gap-2 mb-4">
                <Bell className="w-5 h-5 text-orange-600" />
                <h2 className="text-lg font-semibold">알림 설정</h2>
              </div>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium text-gray-700">
                    이메일 알림
                  </label>
                  <input
                    type="checkbox"
                    checked={settings.notifications.emailEnabled}
                    onChange={(e) => updateSetting('notifications', 'emailEnabled', e.target.checked)}
                    className="w-4 h-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                </div>
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium text-gray-700">
                    SMS 알림
                  </label>
                  <input
                    type="checkbox"
                    checked={settings.notifications.smsEnabled}
                    onChange={(e) => updateSetting('notifications', 'smsEnabled', e.target.checked)}
                    className="w-4 h-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                </div>
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium text-gray-700">
                    시스템 경고
                  </label>
                  <input
                    type="checkbox"
                    checked={settings.notifications.systemAlerts}
                    onChange={(e) => updateSetting('notifications', 'systemAlerts', e.target.checked)}
                    className="w-4 h-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                </div>
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium text-gray-700">
                    사용자 알림
                  </label>
                  <input
                    type="checkbox"
                    checked={settings.notifications.userNotifications}
                    onChange={(e) => updateSetting('notifications', 'userNotifications', e.target.checked)}
                    className="w-4 h-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                </div>
              </div>
            </Card>

            {/* API Settings */}
            <Card className="p-6 lg:col-span-2">
              <div className="flex items-center gap-2 mb-4">
                <Key className="w-5 h-5 text-purple-600" />
                <h2 className="text-lg font-semibold">API 설정</h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    요청 제한 (시간당)
                  </label>
                  <input
                    type="number"
                    value={settings.api.rateLimit}
                    onChange={(e) => updateSetting('api', 'rateLimit', parseInt(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    min="100"
                    max="10000"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    API 버전
                  </label>
                  <select
                    value={settings.api.apiVersion}
                    onChange={(e) => updateSetting('api', 'apiVersion', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="v1">v1</option>
                    <option value="v2">v2</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    로그 레벨
                  </label>
                  <select
                    value={settings.api.logLevel}
                    onChange={(e) => updateSetting('api', 'logLevel', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="debug">Debug</option>
                    <option value="info">Info</option>
                    <option value="warn">Warning</option>
                    <option value="error">Error</option>
                  </select>
                </div>
              </div>
            </Card>
          </div>

          {/* Status Message */}
          {hasChanges && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <p className="text-sm text-yellow-800">
                변경된 설정이 있습니다. 저장 버튼을 클릭하여 변경사항을 적용하세요.
              </p>
            </div>
          )}
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  );
}