'use client';

import { useState } from 'react';
import { Search, Plus, Edit, Trash2, Shield, ShieldCheck } from 'lucide-react';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { useLanguage } from '@/contexts/LanguageContext';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { DeleteConfirmModal } from '@/components/admin/DeleteConfirmModal';
import { UserFormModal } from '@/components/admin/UserFormModal';

interface User {
  id: string;
  name: string;
  email: string;
  company: string;
  role: 'admin' | 'user';
  status: 'active' | 'inactive';
  lastLogin: string;
}

const mockUsers: User[] = [
  {
    id: '1',
    name: '김철수',
    email: 'kim@company-a.com',
    company: '(주)무역회사A',
    role: 'admin',
    status: 'active',
    lastLogin: '2024-01-15 14:30'
  },
  {
    id: '2',
    name: '이영희',
    email: 'lee@company-b.com',
    company: '글로벌무역B',
    role: 'user',
    status: 'active',
    lastLogin: '2024-01-15 09:15'
  },
  {
    id: '3',
    name: '박민수',
    email: 'park@company-c.com',
    company: '한국트레이딩C',
    role: 'user',
    status: 'inactive',
    lastLogin: '2024-01-10 16:45'
  }
];

export default function UsersPage() {
  const { t } = useLanguage();
  const [users, setUsers] = useState<User[]>(mockUsers);
  const [searchTerm, setSearchTerm] = useState('');
  const [userFormModal, setUserFormModal] = useState<{ isOpen: boolean; user: User | null }>({ isOpen: false, user: null });
  const [deleteModal, setDeleteModal] = useState<{ isOpen: boolean; user: User | null }>({ isOpen: false, user: null });
  const [isDeleting, setIsDeleting] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  const filteredUsers = users.filter(user =>
    user.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.company.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getStatusColor = (status: string) => {
    return status === 'active' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800';
  };

  const getRoleIcon = (role: string) => {
    return role === 'admin' ? ShieldCheck : Shield;
  };

  const handleAddUser = () => {
    setUserFormModal({ isOpen: true, user: null });
  };

  const handleEditUser = (user: User) => {
    setUserFormModal({ isOpen: true, user });
  };

  const handleUserFormClose = () => {
    if (isSaving) return;
    setUserFormModal({ isOpen: false, user: null });
  };

  const handleUserFormSave = async (userData: any) => {
    setIsSaving(true);
    
    // 시뮬레이션 지연
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    if (userFormModal.user) {
      // 수정 모드
      setUsers(prev => prev.map(user => 
        user.id === userFormModal.user!.id 
          ? { ...user, ...userData, lastLogin: user.lastLogin }
          : user
      ));
    } else {
      // 추가 모드
      const newUser: User = {
        id: Date.now().toString(),
        ...userData,
        lastLogin: '방금 전'
      };
      setUsers(prev => [...prev, newUser]);
    }
    
    setIsSaving(false);
    setUserFormModal({ isOpen: false, user: null });
    // TODO: API 호출로 서버에 저장/업데이트
  };

  const handleDeleteClick = (user: User) => {
    setDeleteModal({ isOpen: true, user });
  };

  const handleDeleteConfirm = async () => {
    if (!deleteModal.user) return;
    
    setIsDeleting(true);
    
    // 시뮬레이션 지연
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    setUsers(prev => prev.filter(u => u.id !== deleteModal.user!.id));
    setDeleteModal({ isOpen: false, user: null });
    setIsDeleting(false);
    // TODO: API 호출로 서버에서 삭제
  };

  const handleDeleteCancel = () => {
    if (isDeleting) return;
    setDeleteModal({ isOpen: false, user: null });
  };

  return (
    <ProtectedRoute requiredRole="admin">
      <DashboardLayout isAdmin={true}>
        <div className="space-y-6">
        {/* Page Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h1 className="text-2xl font-bold text-foreground">
              {t('admin.userManagement')}
            </h1>
            <p className="text-muted-foreground">
              사용자 계정을 관리하고 권한을 설정하세요
            </p>
          </div>
          <Button className="gap-2" onClick={handleAddUser}>
            <Plus className="w-4 h-4" />
            새 사용자 추가
          </Button>
        </div>

        {/* Search and Filters */}
        <Card className="p-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="이름, 이메일, 회사명으로 검색..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <div className="flex gap-2">
              <Button variant="outline">전체</Button>
              <Button variant="outline">활성</Button>
              <Button variant="outline">비활성</Button>
            </div>
          </div>
        </Card>

        {/* Users Table */}
        <Card className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    사용자
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    회사
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    권한
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    상태
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    마지막 로그인
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    작업
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredUsers.map((user) => {
                  const RoleIcon = getRoleIcon(user.role);
                  
                  return (
                    <tr key={user.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="flex-shrink-0 h-10 w-10">
                            <div className="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center">
                              <span className="text-sm font-medium text-blue-600">
                                {user.name.charAt(0)}
                              </span>
                            </div>
                          </div>
                          <div className="ml-4">
                            <div className="text-sm font-medium text-gray-900">{user.name}</div>
                            <div className="text-sm text-gray-500">{user.email}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{user.company}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <RoleIcon className="w-4 h-4 mr-2 text-gray-600" />
                          <span className="text-sm text-gray-900 capitalize">
                            {user.role === 'admin' ? '관리자' : '사용자'}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(user.status)}`}>
                          {user.status === 'active' ? '활성' : '비활성'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {user.lastLogin}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <div className="flex space-x-2">
                          <Button 
                            variant="ghost" 
                            size="sm"
                            onClick={() => handleEditUser(user)}
                            className="text-blue-600 hover:text-blue-800"
                          >
                            <Edit className="w-4 h-4" />
                          </Button>
                          <Button 
                            variant="ghost" 
                            size="sm" 
                            onClick={() => handleDeleteClick(user)}
                            className="text-red-600 hover:text-red-800"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Card>

        {/* Pagination */}
        <div className="flex items-center justify-between">
          <div className="text-sm text-gray-700">
            총 {filteredUsers.length}명의 사용자
          </div>
          <div className="flex space-x-2">
            <Button variant="outline" size="sm" disabled>
              이전
            </Button>
            <Button variant="outline" size="sm" className="bg-blue-600 text-white">
              1
            </Button>
            <Button variant="outline" size="sm">
              다음
            </Button>
          </div>
        </div>
        </div>
        
        {/* User Form Modal (Add/Edit) */}
        <UserFormModal
          isOpen={userFormModal.isOpen}
          onClose={handleUserFormClose}
          onSave={handleUserFormSave}
          user={userFormModal.user}
          isLoading={isSaving}
        />
        
        {/* Delete Confirmation Modal */}
        <DeleteConfirmModal
          isOpen={deleteModal.isOpen}
          onClose={handleDeleteCancel}
          onConfirm={handleDeleteConfirm}
          userName={deleteModal.user?.name || ''}
          userEmail={deleteModal.user?.email || ''}
          isLoading={isDeleting}
        />
      </DashboardLayout>
    </ProtectedRoute>
  );
}