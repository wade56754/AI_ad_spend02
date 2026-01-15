/**
 * UsersPage Component
 *
 * 用户管理页面 - 使用真实 API
 *
 * SoT References:
 * - API_SOT.md v9.0 §5 Users API
 *
 * Author: AI 代码工厂 v2.4
 */

'use client';

import React, { useState, useCallback } from 'react';
import {
  Users,
  UserPlus,
  Search,
  Edit,
  Trash2,
  Shield,
  Mail,
  Calendar,
  RefreshCw,
  X,
  AlertCircle,
  CheckCircle,
  Loader2,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  useUsers,
  useCreateUser,
  useUpdateUser,
  useDeleteUser,
  useToggleUserStatus,
} from '../hooks';
import {
  USER_ROLE_OPTIONS,
  UserRole,
  type User,
  type CreateUserRequest,
  type UpdateUserRequest,
} from '../types';

// === Helper Functions ===

function getRoleConfig(role: UserRole) {
  return USER_ROLE_OPTIONS.find((r) => r.value === role) || USER_ROLE_OPTIONS[4];
}

function formatDate(dateString: string | null | undefined) {
  if (!dateString) return '-';
  return new Date(dateString).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

// === Sub Components ===

interface CreateUserModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: CreateUserRequest) => void;
  isLoading: boolean;
}

function CreateUserModal({ isOpen, onClose, onSubmit, isLoading }: CreateUserModalProps) {
  const [formData, setFormData] = useState<CreateUserRequest>({
    email: '',
    password: '',
    username: '',
    full_name: '',
    role: UserRole.PITCHER,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">添加用户</h3>
          <Button
            onClick={onClose}
            variant="ghost"
            size="icon"
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="h-5 w-5" />
          </Button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              用户名 <span className="text-red-500">*</span>
            </label>
            <Input
              type="text"
              required
              minLength={2}
              maxLength={50}
              value={formData.username}
              onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              className="border-gray-300 rounded-lg focus-visible:ring-purple-500"
              placeholder="请输入用户名"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              邮箱 <span className="text-red-500">*</span>
            </label>
            <Input
              type="email"
              required
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="border-gray-300 rounded-lg focus-visible:ring-purple-500"
              placeholder="请输入邮箱"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              密码 <span className="text-red-500">*</span>
            </label>
            <Input
              type="password"
              required
              minLength={8}
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              className="border-gray-300 rounded-lg focus-visible:ring-purple-500"
              placeholder="请输入密码（至少8位）"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">真实姓名</label>
            <Input
              type="text"
              value={formData.full_name || ''}
              onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
              className="border-gray-300 rounded-lg focus-visible:ring-purple-500"
              placeholder="请输入真实姓名"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              角色 <span className="text-red-500">*</span>
            </label>
            <Select
              value={formData.role}
              onValueChange={(value) => setFormData({ ...formData, role: value as UserRole })}
            >
              <SelectTrigger className="border-gray-300 rounded-lg focus:ring-purple-500">
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

          <div className="flex gap-3 pt-4">
            <Button type="button" onClick={onClose} variant="outline" className="flex-1 rounded-lg">
              取消
            </Button>
            <Button
              type="submit"
              disabled={isLoading}
              className="flex-1 rounded-lg bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {isLoading && <Loader2 className="h-4 w-4 animate-spin" />}
              创建
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

interface EditUserModalProps {
  user: User | null;
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (id: string, data: UpdateUserRequest) => void;
  isLoading: boolean;
}

function EditUserModal({ user, isOpen, onClose, onSubmit, isLoading }: EditUserModalProps) {
  const [formData, setFormData] = useState<UpdateUserRequest>({});

  React.useEffect(() => {
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

  if (!isOpen || !user) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">编辑用户</h3>
          <Button
            onClick={onClose}
            variant="ghost"
            size="icon"
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="h-5 w-5" />
          </Button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">用户名</label>
            <Input
              type="text"
              value={formData.username || ''}
              onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              className="border-gray-300 rounded-lg focus-visible:ring-purple-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">真实姓名</label>
            <Input
              type="text"
              value={formData.full_name || ''}
              onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
              className="border-gray-300 rounded-lg focus-visible:ring-purple-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">角色</label>
            <Select
              value={formData.role || user.role}
              onValueChange={(value) => setFormData({ ...formData, role: value as UserRole })}
            >
              <SelectTrigger className="border-gray-300 rounded-lg focus:ring-purple-500">
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

          <div className="flex items-center gap-2">
            <Checkbox
              id="is_active"
              checked={formData.is_active ?? user.is_active}
              onCheckedChange={(checked) =>
                setFormData({ ...formData, is_active: checked === true })
              }
              className="border-gray-300 data-[state=checked]:bg-purple-600 data-[state=checked]:border-purple-600"
            />
            <label htmlFor="is_active" className="text-sm text-gray-700">
              账号激活
            </label>
          </div>

          <div className="flex gap-3 pt-4">
            <Button type="button" onClick={onClose} variant="outline" className="flex-1 rounded-lg">
              取消
            </Button>
            <Button
              type="submit"
              disabled={isLoading}
              className="flex-1 rounded-lg bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {isLoading && <Loader2 className="h-4 w-4 animate-spin" />}
              保存
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

interface DeleteConfirmModalProps {
  user: User | null;
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  isLoading: boolean;
}

function DeleteConfirmModal({
  user,
  isOpen,
  onClose,
  onConfirm,
  isLoading,
}: DeleteConfirmModalProps) {
  if (!isOpen || !user) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-sm">
        <div className="flex items-center gap-3 mb-4">
          <div className="h-10 w-10 rounded-full bg-red-100 flex items-center justify-center">
            <AlertCircle className="h-5 w-5 text-red-600" />
          </div>
          <h3 className="text-lg font-semibold">确认删除</h3>
        </div>

        <p className="text-gray-600 mb-6">
          确定要删除用户 <strong>{user.full_name || user.username}</strong>{' '}
          吗？此操作将禁用该用户账号。
        </p>

        <div className="flex gap-3">
          <Button onClick={onClose} variant="outline" className="flex-1 rounded-lg">
            取消
          </Button>
          <Button
            onClick={onConfirm}
            disabled={isLoading}
            variant="destructive"
            className="flex-1 rounded-lg flex items-center justify-center gap-2"
          >
            {isLoading && <Loader2 className="h-4 w-4 animate-spin" />}
            删除
          </Button>
        </div>
      </div>
    </div>
  );
}

// === Main Component ===

export function UsersPage() {
  // State
  const [searchQuery, setSearchQuery] = useState('');
  const [roleFilter, setRoleFilter] = useState<string>('');
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);

  // Modal states
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [deletingUser, setDeletingUser] = useState<User | null>(null);

  // Toast state
  const [toast, setToast] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // Queries
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

  // Mutations
  const createMutation = useCreateUser({
    onSuccess: () => {
      setShowCreateModal(false);
      showToast('success', '用户创建成功');
    },
    onError: (err) => {
      showToast('error', err.message || '创建失败');
    },
  });

  const updateMutation = useUpdateUser({
    onSuccess: () => {
      setEditingUser(null);
      showToast('success', '用户更新成功');
    },
    onError: (err) => {
      showToast('error', err.message || '更新失败');
    },
  });

  const deleteMutation = useDeleteUser({
    onSuccess: () => {
      setDeletingUser(null);
      showToast('success', '用户删除成功');
    },
    onError: (err) => {
      showToast('error', err.message || '删除失败');
    },
  });

  // Handlers
  const showToast = useCallback((type: 'success' | 'error', message: string) => {
    setToast({ type, message });
    setTimeout(() => setToast(null), 3000);
  }, []);

  const handleCreate = (data: CreateUserRequest) => {
    createMutation.mutate(data);
  };

  const handleUpdate = (id: string, data: UpdateUserRequest) => {
    updateMutation.mutate({ id, data });
  };

  const handleDelete = () => {
    if (deletingUser) {
      deleteMutation.mutate(deletingUser.id);
    }
  };

  // Extract users from response
  const users = usersData?.items || usersData?.data || [];
  const total = usersData?.total || usersData?.meta?.total || 0;
  const totalPages = usersData?.total_pages || usersData?.meta?.total_pages || 1;

  return (
    <div className="min-h-screen bg-gray-50" data-testid="pitcher-page">
      {/* Toast */}
      {toast && (
        <div
          className={`fixed top-4 right-4 z-50 flex items-center gap-2 px-4 py-3 rounded-lg shadow-lg ${
            toast.type === 'success' ? 'bg-green-500' : 'bg-red-500'
          } text-white`}
        >
          {toast.type === 'success' ? (
            <CheckCircle className="h-5 w-5" />
          ) : (
            <AlertCircle className="h-5 w-5" />
          )}
          {toast.message}
        </div>
      )}

      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Users className="h-8 w-8 text-purple-600" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">投手管理</h1>
                <p className="text-sm text-gray-500">管理系统用户账号和权限</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Button
                onClick={() => refetch()}
                disabled={isLoading}
                variant="outline"
                className="gap-2 rounded-lg"
              >
                <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
                刷新
              </Button>
              <Button
                onClick={() => setShowCreateModal(true)}
                className="gap-2 rounded-lg bg-purple-600 text-white hover:bg-purple-700"
                data-testid="create-btn"
              >
                <UserPlus className="h-4 w-4" />
                添加用户
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Filters - v3.0 */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="bg-white rounded-xl shadow-sm p-4" data-testid="pitcher-filters">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex-1 min-w-[200px]" data-testid="search-filter">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  type="text"
                  placeholder="搜索用户名、邮箱..."
                  value={searchQuery}
                  onChange={(e) => {
                    setSearchQuery(e.target.value);
                    setPage(1);
                  }}
                  className="pl-10 pr-4 border-gray-300 rounded-lg focus-visible:ring-purple-500"
                />
              </div>
            </div>
            <Select
              value={roleFilter || 'all'}
              onValueChange={(value) => {
                setRoleFilter(value === 'all' ? '' : value);
                setPage(1);
              }}
            >
              <SelectTrigger
                className="border-gray-300 rounded-lg focus:ring-purple-500"
                data-testid="role-filter"
              >
                <SelectValue placeholder="全部角色" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部角色</SelectItem>
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

      {/* Content - v3.0 */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 pb-8">
        {isError ? (
          <div className="bg-white rounded-xl shadow-sm p-8 text-center">
            <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">加载失败</h3>
            <p className="text-gray-500 mb-4">{(error as Error)?.message || '请稍后重试'}</p>
            <Button
              onClick={() => refetch()}
              className="rounded-lg bg-purple-600 text-white hover:bg-purple-700"
            >
              重试
            </Button>
          </div>
        ) : (
          <div
            className="bg-white rounded-xl shadow-sm overflow-hidden"
            data-testid="pitcher-table"
          >
            {isLoading ? (
              <div
                className="flex items-center justify-center py-12"
                data-testid="loading-skeleton"
              >
                <Loader2 className="h-8 w-8 text-purple-600 animate-spin" />
              </div>
            ) : (
              <>
                <Table>
                  <TableHeader className="bg-gray-50">
                    <TableRow>
                      <TableHead className="px-6 py-3 text-xs font-medium text-gray-500 uppercase">
                        用户
                      </TableHead>
                      <TableHead className="px-6 py-3 text-xs font-medium text-gray-500 uppercase">
                        邮箱
                      </TableHead>
                      <TableHead className="px-6 py-3 text-xs font-medium text-gray-500 uppercase">
                        角色
                      </TableHead>
                      <TableHead className="px-6 py-3 text-xs font-medium text-gray-500 uppercase">
                        状态
                      </TableHead>
                      <TableHead className="px-6 py-3 text-xs font-medium text-gray-500 uppercase">
                        创建时间
                      </TableHead>
                      <TableHead className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                        操作
                      </TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody className="bg-white divide-y divide-gray-200">
                    {users.map((user: User) => {
                      const roleConfig = getRoleConfig(user.role);

                      return (
                        <TableRow key={user.id} className="hover:bg-gray-50">
                          <TableCell className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center">
                              <div className="h-10 w-10 flex-shrink-0">
                                <div className="h-10 w-10 rounded-full bg-purple-100 flex items-center justify-center">
                                  <span className="text-purple-600 font-medium">
                                    {user.full_name?.[0] || user.username[0].toUpperCase()}
                                  </span>
                                </div>
                              </div>
                              <div className="ml-4">
                                <div className="text-sm font-medium text-gray-900">
                                  {user.full_name || user.username}
                                </div>
                                <div className="text-sm text-gray-500">@{user.username}</div>
                              </div>
                            </div>
                          </TableCell>
                          <TableCell className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center text-sm text-gray-600">
                              <Mail className="h-4 w-4 mr-2 text-gray-400" />
                              {user.email}
                            </div>
                          </TableCell>
                          <TableCell className="px-6 py-4 whitespace-nowrap">
                            <span
                              className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${
                                roleConfig.color === 'red'
                                  ? 'bg-red-100 text-red-700'
                                  : roleConfig.color === 'green'
                                    ? 'bg-green-100 text-green-700'
                                    : roleConfig.color === 'blue'
                                      ? 'bg-blue-100 text-blue-700'
                                      : roleConfig.color === 'purple'
                                        ? 'bg-purple-100 text-purple-700'
                                        : 'bg-orange-100 text-orange-700'
                              }`}
                            >
                              <Shield className="h-3 w-3" />
                              {roleConfig.label}
                            </span>
                          </TableCell>
                          <TableCell className="px-6 py-4 whitespace-nowrap">
                            <span
                              className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${
                                user.is_active
                                  ? 'bg-green-100 text-green-700'
                                  : 'bg-gray-100 text-gray-700'
                              }`}
                            >
                              {user.is_active ? '正常' : '已停用'}
                            </span>
                          </TableCell>
                          <TableCell className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            <div className="flex items-center">
                              <Calendar className="h-4 w-4 mr-2 text-gray-400" />
                              {formatDate(user.created_at)}
                            </div>
                          </TableCell>
                          <TableCell className="px-6 py-4 whitespace-nowrap text-right">
                            <div className="flex items-center justify-end gap-2">
                              <Button
                                onClick={() => setEditingUser(user)}
                                variant="ghost"
                                size="icon"
                                className="text-gray-400 hover:text-blue-600"
                                title="编辑"
                              >
                                <Edit className="h-4 w-4" />
                              </Button>
                              <Button
                                onClick={() => setDeletingUser(user)}
                                variant="ghost"
                                size="icon"
                                className="text-gray-400 hover:text-red-600"
                                title="删除"
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>

                {users.length === 0 && (
                  <div className="py-12 text-center text-gray-500">暂无用户数据</div>
                )}

                {/* Pagination */}
                <div className="px-6 py-4 border-t flex items-center justify-between">
                  <div className="text-sm text-gray-500">共 {total} 个用户</div>
                  <div className="flex items-center gap-2">
                    <Button
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
                      disabled={page <= 1}
                      variant="outline"
                      size="sm"
                    >
                      上一页
                    </Button>
                    <span className="text-sm text-gray-600">
                      {page} / {totalPages}
                    </span>
                    <Button
                      onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                      disabled={page >= totalPages}
                      variant="outline"
                      size="sm"
                    >
                      下一页
                    </Button>
                  </div>
                </div>
              </>
            )}
          </div>
        )}
      </div>

      {/* Modals */}
      <CreateUserModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSubmit={handleCreate}
        isLoading={createMutation.isPending}
      />

      <EditUserModal
        user={editingUser}
        isOpen={!!editingUser}
        onClose={() => setEditingUser(null)}
        onSubmit={handleUpdate}
        isLoading={updateMutation.isPending}
      />

      <DeleteConfirmModal
        user={deletingUser}
        isOpen={!!deletingUser}
        onClose={() => setDeletingUser(null)}
        onConfirm={handleDelete}
        isLoading={deleteMutation.isPending}
      />
    </div>
  );
}

export default UsersPage;
