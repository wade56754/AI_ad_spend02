/**
 * UsersTable Component
 *
 * 用户表格 - 从 UsersPage.tsx 提取
 * 使用 shadcn/ui Table 组件
 */

'use client';

import React from 'react';
import { Edit, Trash2, Shield, Mail, Calendar, Loader2, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { ScrollArea, ScrollBar } from '@/components/ui/scroll-area';
import type { User } from '../types';
import { getRoleConfig, formatDate, getRoleBadgeClass } from '../utils/usersHelpers';

interface UsersTableProps {
  users: User[];
  isLoading: boolean;
  isError: boolean;
  error?: Error | null;
  onEdit: (user: User) => void;
  onDelete: (user: User) => void;
  onRetry?: () => void;
  // Pagination
  page: number;
  totalPages: number;
  total: number;
  onPageChange: (page: number) => void;
}

export function UsersTable({
  users,
  isLoading,
  isError,
  error,
  onEdit,
  onDelete,
  onRetry,
  page,
  totalPages,
  total,
  onPageChange,
}: UsersTableProps) {
  if (isError) {
    return (
      <div className="bg-white rounded-xl shadow-sm p-8 text-center">
        <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">加载失败</h3>
        <p className="text-gray-500 mb-4">{error?.message || '请稍后重试'}</p>
        {onRetry && (
          <Button onClick={onRetry}>
            重试
          </Button>
        )}
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl shadow-sm">
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 text-purple-600 animate-spin" />
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm overflow-hidden">
      <ScrollArea className="w-full">
        <Table>
          <TableHeader>
            <TableRow className="bg-gray-50">
              <TableHead className="px-6 py-3">用户</TableHead>
              <TableHead className="px-6 py-3">邮箱</TableHead>
              <TableHead className="px-6 py-3">角色</TableHead>
              <TableHead className="px-6 py-3">状态</TableHead>
              <TableHead className="px-6 py-3">创建时间</TableHead>
              <TableHead className="px-6 py-3 text-right">操作</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {users.map((user) => {
              const roleConfig = getRoleConfig(user.role);

              return (
                <TableRow key={user.id} className="hover:bg-gray-50">
                  <TableCell className="px-6 py-4">
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
                  <TableCell className="px-6 py-4">
                    <div className="flex items-center text-sm text-gray-600">
                      <Mail className="h-4 w-4 mr-2 text-gray-400" />
                      {user.email}
                    </div>
                  </TableCell>
                  <TableCell className="px-6 py-4">
                    <Badge className={`${getRoleBadgeClass(roleConfig.color)} inline-flex items-center gap-1`}>
                      <Shield className="h-3 w-3" />
                      {roleConfig.label}
                    </Badge>
                  </TableCell>
                  <TableCell className="px-6 py-4">
                    <Badge variant={user.is_active ? 'default' : 'secondary'}>
                      {user.is_active ? '正常' : '已停用'}
                    </Badge>
                  </TableCell>
                  <TableCell className="px-6 py-4 text-sm text-gray-500">
                    <div className="flex items-center">
                      <Calendar className="h-4 w-4 mr-2 text-gray-400" />
                      {formatDate(user.created_at)}
                    </div>
                  </TableCell>
                  <TableCell className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onEdit(user)}
                        title="编辑"
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onDelete(user)}
                        title="删除"
                        className="text-red-600 hover:text-red-700"
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
        <ScrollBar orientation="horizontal" />
      </ScrollArea>

      {users.length === 0 && (
        <div className="py-12 text-center text-gray-500">暂无用户数据</div>
      )}

      {/* Pagination */}
      <div className="px-6 py-4 border-t flex items-center justify-between">
        <div className="text-sm text-gray-500">共 {total} 个用户</div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onPageChange(Math.max(1, page - 1))}
            disabled={page <= 1}
          >
            上一页
          </Button>
          <span className="text-sm text-gray-600">
            {page} / {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onPageChange(Math.min(totalPages, page + 1))}
            disabled={page >= totalPages}
          >
            下一页
          </Button>
        </div>
      </div>
    </div>
  );
}

export default UsersTable;
