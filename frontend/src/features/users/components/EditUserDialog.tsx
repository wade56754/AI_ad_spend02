/**
 * EditUserDialog Component
 *
 * 编辑用户对话框 - 从 UsersPage.tsx 提取
 * 使用 shadcn/ui Dialog 组件
 */

'use client';

import React, { useState, useEffect } from 'react';
import { Loader2 } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { USER_ROLE_OPTIONS, UserRole, type User, type UpdateUserRequest } from '../types';

interface EditUserDialogProps {
  user: User | null;
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (id: string, data: UpdateUserRequest) => void;
  isLoading: boolean;
}

export function EditUserDialog({ user, isOpen, onClose, onSubmit, isLoading }: EditUserDialogProps) {
  const [formData, setFormData] = useState<UpdateUserRequest>({});

  useEffect(() => {
    if (user) {
      setFormData({
        username: user.username,
        full_name: user.full_name || '',
        role: user.role,
        is_active: user.is_active,
      });
    }
  }, [user]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (user) {
      onSubmit(user.id, formData);
    }
  };

  const handleOpenChange = (open: boolean) => {
    if (!open) {
      onClose();
    }
  };

  if (!user) return null;

  return (
    <Dialog open={isOpen} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>编辑用户</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="edit-username">用户名</Label>
            <Input
              id="edit-username"
              type="text"
              value={formData.username || ''}
              onChange={(e) => setFormData({ ...formData, username: e.target.value })}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="edit-full_name">真实姓名</Label>
            <Input
              id="edit-full_name"
              type="text"
              value={formData.full_name || ''}
              onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="edit-role">角色</Label>
            <Select
              value={formData.role || user.role}
              onValueChange={(value) => setFormData({ ...formData, role: value as UserRole })}
            >
              <SelectTrigger>
                <SelectValue placeholder="选择角色" />
              </SelectTrigger>
              <SelectContent>
                {USER_ROLE_OPTIONS.map((role) => (
                  <SelectItem key={role.value} value={role.value}>
                    {role.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center space-x-2">
            <Checkbox
              id="is_active"
              checked={formData.is_active ?? user.is_active}
              onCheckedChange={(checked) => setFormData({ ...formData, is_active: !!checked })}
            />
            <Label htmlFor="is_active" className="text-sm font-normal">
              账号激活
            </Label>
          </div>

          <div className="flex gap-3 pt-4">
            <Button type="button" variant="outline" className="flex-1" onClick={onClose}>
              取消
            </Button>
            <Button type="submit" className="flex-1" disabled={isLoading}>
              {isLoading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              保存
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}

export default EditUserDialog;
