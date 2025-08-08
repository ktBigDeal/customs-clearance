'use client';

import { useState } from 'react';
import { AlertTriangle, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

interface DeleteConfirmModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  userName: string;
  userEmail: string;
  isLoading?: boolean;
}

export function DeleteConfirmModal({
  isOpen,
  onClose,
  onConfirm,
  userName,
  userEmail,
  isLoading = false
}: DeleteConfirmModalProps) {
  const [confirmText, setConfirmText] = useState('');
  const expectedText = '삭제 확인';

  const handleConfirm = () => {
    if (confirmText === expectedText) {
      onConfirm();
    }
  };

  const isConfirmDisabled = confirmText !== expectedText || isLoading;

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />
      
      {/* Modal */}
      <Card className="relative w-full max-w-md p-6 bg-white shadow-xl">
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1 hover:bg-gray-100 rounded"
          disabled={isLoading}
        >
          <X className="w-4 h-4" />
        </button>

        {/* Warning icon and title */}
        <div className="flex items-center gap-3 mb-4">
          <div className="flex-shrink-0 w-12 h-12 bg-red-100 rounded-full flex items-center justify-center">
            <AlertTriangle className="w-6 h-6 text-red-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              사용자 삭제 확인
            </h3>
            <p className="text-sm text-gray-500">
              이 작업은 되돌릴 수 없습니다
            </p>
          </div>
        </div>

        {/* User info */}
        <div className="mb-6 p-4 bg-gray-50 rounded-lg border">
          <div className="space-y-1">
            <p className="font-medium text-gray-900">{userName}</p>
            <p className="text-sm text-gray-600">{userEmail}</p>
          </div>
        </div>

        {/* Warning message */}
        <div className="mb-6">
          <p className="text-sm text-gray-700 mb-3">
            다음 사용자를 완전히 삭제하시겠습니까?
          </p>
          <ul className="text-sm text-gray-600 space-y-1 ml-4 list-disc">
            <li>사용자 계정이 영구적으로 삭제됩니다</li>
            <li>연관된 신고서 데이터는 유지됩니다</li>
            <li>삭제된 계정은 복구할 수 없습니다</li>
          </ul>
        </div>

        {/* Confirmation input */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            삭제를 확인하려면 "<span className="font-semibold text-red-600">{expectedText}</span>"를 입력하세요
          </label>
          <input
            type="text"
            value={confirmText}
            onChange={(e) => setConfirmText(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
            placeholder={expectedText}
            disabled={isLoading}
          />
        </div>

        {/* Actions */}
        <div className="flex space-x-3">
          <Button
            variant="outline"
            onClick={onClose}
            className="flex-1"
            disabled={isLoading}
          >
            취소
          </Button>
          <Button
            onClick={handleConfirm}
            disabled={isConfirmDisabled}
            className="flex-1 bg-red-600 hover:bg-red-700 text-white"
          >
            {isLoading ? (
              <div className="flex items-center space-x-2">
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                <span>삭제 중...</span>
              </div>
            ) : (
              '삭제 확인'
            )}
          </Button>
        </div>
      </Card>
    </div>
  );
}