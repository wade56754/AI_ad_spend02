/**
 * UsersPage (Refactored)
 *
 * 用户管理页面 - 从 722 行重构为 ~150 行
 * 子组件已提取到独立文件
 *
 * SoT References:
 * - API_SOT.md v9.0 §5 Users API
 * - C2-pitcher-mgmt.md 模块规格
 */

'use client';

import React, { useState, useCallback } from 'react';
import { Users, UserPlus, Search, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  useUsers,
  useCreateUser,
  useUpdateUser,
  useDeleteUser,
} from '../hooks';
import {
  USER_ROLE_OPTIONS,
  UserRole,
  type User,
  type CreateUserRequest,
  type UpdateUserRequest,
} from '../types';
import { UsersTable } from './UsersTable';
import { CreateUserDialog } from './CreateUserDialog';
import { EditUserDialog } from './EditUserDialog';
import { DeleteUserDialog } from './DeleteUserDialog';

export function UsersPageRefactored() {
  // ============ State ============
  const [searchQuery, setSearchQuery] = useState('');
  const [roleFilter, setRoleFilter] = useState<string>('');
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);

  // Modal states
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [deletingUser, setDeletingUser] = useState<User | null>(null);

  // ============ Queries ============
  const {
    data: usersData,
    isLoading,
    isError,
    error,
    refetch,
  } = useUsers({
    page,
    page_size: pageSize,
    role: roleFilter ? (roleFilter as UserRole) : undefined,
    search: searchQuery || undefined,
  });

  // ============ Mutations ============
  const createMutation = useCreateUser({
    onSuccess: () => {
      setShowCreateModal(false);
      toast.success('用户创建成功');
    },
    onError: (err) => {
      toast.error(err.message || '创建失败');
    },
  });

  const updateMutation = useUpdateUser({
    onSuccess: () => {
      setEditingUser(null);
      toast.success('用户更新成功');
    },
    onError: (err) => {
      toast.error(err.message || '更新失败');
    },
  });

  const deleteMutation = useDeleteUser({
    onSuccess: () => {
      setDeletingUser(null);
      toast.success('用户删除成功');
    },
    onError: (err) => {
      toast.error(err.message || '删除失败');
    },
  });

  // ============ Handlers ============
  const handleCreate = useCallback((data: CreateUserRequest) => {
    createMutation.mutate(data);
  }, [createMutation]);

  const handleUpdate = useCallback((id: string, data: UpdateUserRequest) => {
    updateMutation.mutate({ id, data });
  }, [updateMutation]);

  const handleDelete = useCallback(() => {
    if (deletingUser) {
      deleteMutation.mutate(deletingUser.id);
    }
  }, [deletingUser, deleteMutation]);

  const handleSearchChange = useCallback((value: string) => {
    setSearchQuery(value);
    setPage(1);
  }, []);

  const handleRoleFilterChange = useCallback((value: string) => {
    setRoleFilter(value === '__all__' ? '' : value);
    setPage(1);
  }, []);

  // ============ Computed ============
  const users = usersData?.items || usersData?.data || [];
  const total = usersData?.total || usersData?.meta?.total || 0;
  const totalPages = usersData?.total_pages || usersData?.meta?.total_pages || 1;

  // ============ Render ============
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Users className="h-8 w-8 text-purple-600" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">用户管理</h1>
                <p className="text-sm text-gray-500">管理系统用户账号和权限</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Button variant="outline" onClick={() => refetch()} disabled={isLoading}>
                <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
                刷新
              </Button>
              <Button onClick={() => setShowCreateModal(true)}>
                <UserPlus className="h-4 w-4 mr-2" />
                添加用户
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="bg-white rounded-xl shadow-sm p-4">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex-1 min-w-[200px] relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="搜索用户名、邮箱..."
                value={searchQuery}
                onChange={(e) => handleSearchChange(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={roleFilter || '__all__'} onValueChange={handleRoleFilterChange}>
              <SelectTrigger className="w-[160px]">
                <SelectValue placeholder="全部角色" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__all__">全部角色</SelectItem>
                {USER_ROLE_OPTIONS.map((role) => (
                  <SelectItem key={role.value} value={role.value}>
                    {role.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 pb-8">
        <UsersTable
          users={users}
          isLoading={isLoading}
          isError={isError}
          error={error as Error}
          onEdit={setEditingUser}
          onDelete={setDeletingUser}
          onRetry={refetch}
          page={page}
          totalPages={totalPages}
          total={total}
          onPageChange={setPage}
        />
      </div>

      {/* Dialogs */}
      <CreateUserDialog
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSubmit={handleCreate}
        isLoading={createMutation.isPending}
      />

      <EditUserDialog
        user={editingUser}
        isOpen={!!editingUser}
        onClose={() => setEditingUser(null)}
        onSubmit={handleUpdate}
        isLoading={updateMutation.isPending}
      />

      <DeleteUserDialog
        user={deletingUser}
        isOpen={!!deletingUser}
        onClose={() => setDeletingUser(null)}
        onConfirm={handleDelete}
        isLoading={deleteMutation.isPending}
      />
    </div>
  );
}

export default UsersPageRefactored;
