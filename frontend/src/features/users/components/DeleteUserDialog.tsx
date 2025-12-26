/**
 * DeleteUserDialog Component
 *
 * 删除用户确认对话框 - 从 UsersPage.tsx 提取
 * 使用 shadcn/ui AlertDialog 组件
 */

'use client';

import React from 'react';
import { AlertCircle, Loader2 } from 'lucide-react';
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Button } from '@/components/ui/button';
import type { User } from '../types';

interface DeleteUserDialogProps {
  user: User | null;
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  isLoading: boolean;
}

export function DeleteUserDialog({ user, isOpen, onClose, onConfirm, isLoading }: DeleteUserDialogProps) {
  if (!user) return null;

  return (
    <AlertDialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-full bg-red-100 flex items-center justify-center">
              <AlertCircle className="h-5 w-5 text-red-600" />
            </div>
            <AlertDialogTitle>确认删除</AlertDialogTitle>
          </div>
          <AlertDialogDescription>
            确定要删除用户 <strong>{user.full_name || user.username}</strong> 吗？此操作将禁用该用户账号。
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <Button variant="outline" onClick={onClose}>
            取消
          </Button>
          <Button variant="destructive" onClick={onConfirm} disabled={isLoading}>
            {isLoading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
            删除
          </Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}

export default DeleteUserDialog;
