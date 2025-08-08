'use client';

import { useState } from 'react';
import { Search, Plus, Edit, Trash2, Copy, Download, Eye, FileText, Layout, Code } from 'lucide-react';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { useLanguage } from '@/contexts/LanguageContext';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

interface Template {
  id: string;
  name: string;
  type: string;
  category: string;
  description: string;
  createdDate: string;
  lastModified: string;
  status: 'active' | 'draft' | 'deprecated';
  usage: number;
}

const mockTemplates: Template[] = [
  {
    id: '1',
    name: '일반 수입신고서',
    type: 'form',
    category: '수입신고',
    description: '표준 수입신고서 템플릿',
    createdDate: '2024-01-10',
    lastModified: '2024-01-15',
    status: 'active',
    usage: 1250
  },
  {
    id: '2',
    name: '간이 수입신고서',
    type: 'form',
    category: '수입신고',
    description: '소액 물품용 간소화된 신고서',
    createdDate: '2024-01-08',
    lastModified: '2024-01-12',
    status: 'active',
    usage: 890
  },
  {
    id: '3',
    name: '수출신고서',
    type: 'form',
    category: '수출신고',
    description: '일반 수출신고서 템플릿',
    createdDate: '2024-01-05',
    lastModified: '2024-01-10',
    status: 'active',
    usage: 675
  },
  {
    id: '4',
    name: '통관 확인서',
    type: 'document',
    category: '증명서',
    description: '통관 완료 확인서 템플릿',
    createdDate: '2023-12-20',
    lastModified: '2024-01-08',
    status: 'active',
    usage: 320
  },
  {
    id: '5',
    name: '구버전 신고서',
    type: 'form',
    category: '수입신고',
    description: '2023년 구 양식',
    createdDate: '2023-10-15',
    lastModified: '2023-12-01',
    status: 'deprecated',
    usage: 45
  }
];

export default function TemplatesPage() {
  const { t } = useLanguage();
  const [templates] = useState<Template[]>(mockTemplates);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedStatus, setSelectedStatus] = useState('all');

  const filteredTemplates = templates.filter(template => {
    const matchesSearch = 
      template.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      template.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || template.category === selectedCategory;
    const matchesStatus = selectedStatus === 'all' || template.status === selectedStatus;
    
    return matchesSearch && matchesCategory && matchesStatus;
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'draft': return 'bg-yellow-100 text-yellow-800';
      case 'deprecated': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'active': return '활성';
      case 'draft': return '초안';
      case 'deprecated': return '사용중단';
      default: return status;
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'form': return <Layout className="w-5 h-5" />;
      case 'document': return <FileText className="w-5 h-5" />;
      case 'email': return <Code className="w-5 h-5" />;
      default: return <FileText className="w-5 h-5" />;
    }
  };

  const categories = ['all', '수입신고', '수출신고', '증명서', '기타'];
  const statuses = ['all', 'active', 'draft', 'deprecated'];

  return (
    <ProtectedRoute requiredRole="ADMIN">
      <DashboardLayout isAdmin={true}>
        <div className="space-y-6">
          {/* Page Header */}
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
              <h1 className="text-2xl font-bold text-foreground">
                템플릿 관리
              </h1>
              <p className="text-muted-foreground">
                신고서 양식과 문서 템플릿을 관리하세요
              </p>
            </div>
            <Button className="gap-2">
              <Plus className="w-4 h-4" />
              새 템플릿 생성
            </Button>
          </div>

          {/* Search and Filters */}
          <Card className="p-6">
            <div className="flex flex-col lg:flex-row gap-4">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <input
                  type="text"
                  placeholder="템플릿명 또는 설명으로 검색..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div className="flex gap-2">
                <select
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  {categories.map(cat => (
                    <option key={cat} value={cat}>
                      {cat === 'all' ? '모든 카테고리' : cat}
                    </option>
                  ))}
                </select>
                <select
                  value={selectedStatus}
                  onChange={(e) => setSelectedStatus(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  {statuses.map(status => (
                    <option key={status} value={status}>
                      {status === 'all' ? '모든 상태' : getStatusText(status)}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </Card>

          {/* Templates Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredTemplates.map((template) => (
              <Card key={template.id} className="p-6 hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-blue-100 rounded-lg text-blue-600">
                      {getTypeIcon(template.type)}
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900">{template.name}</h3>
                      <p className="text-sm text-gray-500">{template.category}</p>
                    </div>
                  </div>
                  <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(template.status)}`}>
                    {getStatusText(template.status)}
                  </span>
                </div>

                <p className="text-sm text-gray-600 mb-4 line-clamp-2">
                  {template.description}
                </p>

                <div className="space-y-2 text-xs text-gray-500 mb-4">
                  <div className="flex justify-between">
                    <span>생성일:</span>
                    <span>{template.createdDate}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>최종 수정:</span>
                    <span>{template.lastModified}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>사용 횟수:</span>
                    <span className="font-medium">{template.usage.toLocaleString()}회</span>
                  </div>
                </div>

                <div className="flex justify-between items-center pt-4 border-t">
                  <div className="flex space-x-2">
                    <Button variant="ghost" size="sm" className="text-blue-600 hover:text-blue-800">
                      <Eye className="w-4 h-4" />
                    </Button>
                    <Button variant="ghost" size="sm" className="text-green-600 hover:text-green-800">
                      <Copy className="w-4 h-4" />
                    </Button>
                    <Button variant="ghost" size="sm" className="text-purple-600 hover:text-purple-800">
                      <Download className="w-4 h-4" />
                    </Button>
                  </div>
                  <div className="flex space-x-2">
                    <Button variant="ghost" size="sm" className="text-orange-600 hover:text-orange-800">
                      <Edit className="w-4 h-4" />
                    </Button>
                    {template.status === 'deprecated' && (
                      <Button variant="ghost" size="sm" className="text-red-600 hover:text-red-800">
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    )}
                  </div>
                </div>
              </Card>
            ))}
          </div>

          {/* Statistics */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500">전체 템플릿</p>
                  <p className="text-2xl font-bold text-gray-900">{templates.length}</p>
                </div>
                <Layout className="w-8 h-8 text-blue-600" />
              </div>
            </Card>
            <Card className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500">활성 템플릿</p>
                  <p className="text-2xl font-bold text-green-600">
                    {templates.filter(t => t.status === 'active').length}
                  </p>
                </div>
                <Layout className="w-8 h-8 text-green-600" />
              </div>
            </Card>
            <Card className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500">초안</p>
                  <p className="text-2xl font-bold text-yellow-600">
                    {templates.filter(t => t.status === 'draft').length}
                  </p>
                </div>
                <Layout className="w-8 h-8 text-yellow-600" />
              </div>
            </Card>
            <Card className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500">총 사용량</p>
                  <p className="text-2xl font-bold text-purple-600">
                    {templates.reduce((sum, t) => sum + t.usage, 0).toLocaleString()}
                  </p>
                </div>
                <Layout className="w-8 h-8 text-purple-600" />
              </div>
            </Card>
          </div>
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  );
}