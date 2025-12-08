/**
 * UsersPage Component
 *
 * 用户管理页面
 */

'use client';

import React, { useState } from 'react';
import {
  Users,
  UserPlus,
  Search,
  MoreVertical,
  Edit,
  Trash2,
  Shield,
  Mail,
  Calendar,
  RefreshCw,
} from 'lucide-react';
import { USER_ROLE_OPTIONS, USER_STATUS_OPTIONS, UserRole, UserStatus } from '../types';

// Mock data
const mockUsers = [
  {
    id: '1',
    email: 'admin@example.com',
    username: 'admin',
    full_name: '系统管理员',
    role: UserRole.ADMIN,
    status: UserStatus.ACTIVE,
    is_active: true,
    created_at: '2024-01-01T00:00:00Z',
    last_login: '2024-12-08T10:30:00Z',
  },
  {
    id: '2',
    email: 'finance@example.com',
    username: 'finance_user',
    full_name: '财务小王',
    role: UserRole.FINANCE,
    status: UserStatus.ACTIVE,
    is_active: true,
    created_at: '2024-02-15T00:00:00Z',
    last_login: '2024-12-08T09:00:00Z',
  },
  {
    id: '3',
    email: 'operator@example.com',
    username: 'data_op',
    full_name: '数据小李',
    role: UserRole.DATA_OPERATOR,
    status: UserStatus.ACTIVE,
    is_active: true,
    created_at: '2024-03-20T00:00:00Z',
    last_login: '2024-12-07T18:00:00Z',
  },
  {
    id: '4',
    email: 'buyer@example.com',
    username: 'media_buyer1',
    full_name: '投手小张',
    role: UserRole.MEDIA_BUYER,
    status: UserStatus.INACTIVE,
    is_active: false,
    created_at: '2024-06-01T00:00:00Z',
    last_login: null,
  },
];

function getRoleConfig(role: UserRole) {
  return USER_ROLE_OPTIONS.find((r) => r.value === role) || USER_ROLE_OPTIONS[4];
}

function getStatusConfig(status: UserStatus) {
  return USER_STATUS_OPTIONS.find((s) => s.value === status) || USER_STATUS_OPTIONS[0];
}

export function UsersPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [roleFilter, setRoleFilter] = useState<string>('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const filteredUsers = mockUsers.filter((user) => {
    const matchesSearch =
      !searchQuery ||
      user.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
      user.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
      user.full_name?.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesRole = !roleFilter || user.role === roleFilter;

    return matchesSearch && matchesRole;
  });

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await new Promise((resolve) => setTimeout(resolve, 1000));
    setIsRefreshing(false);
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

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
              <button
                onClick={handleRefresh}
                disabled={isRefreshing}
                className="flex items-center gap-2 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
              >
                <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
                刷新
              </button>
              <button
                onClick={() => setShowCreateModal(true)}
                className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
              >
                <UserPlus className="h-4 w-4" />
                添加用户
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="搜索用户名、邮箱..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                />
              </div>
            </div>
            <select
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
            >
              <option value="">全部角色</option>
              {USER_ROLE_OPTIONS.map((role) => (
                <option key={role.value} value={role.value}>
                  {role.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Users Table */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 pb-8">
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  用户
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  邮箱
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  角色
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  状态
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  最后登录
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  创建时间
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  操作
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredUsers.map((user) => {
                const roleConfig = getRoleConfig(user.role);
                const statusConfig = getStatusConfig(user.status);

                return (
                  <tr key={user.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
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
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center text-sm text-gray-600">
                        <Mail className="h-4 w-4 mr-2 text-gray-400" />
                        {user.email}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
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
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${
                          statusConfig.color === 'green'
                            ? 'bg-green-100 text-green-700'
                            : statusConfig.color === 'red'
                            ? 'bg-red-100 text-red-700'
                            : 'bg-gray-100 text-gray-700'
                        }`}
                      >
                        {statusConfig.label}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(user.last_login)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <div className="flex items-center">
                        <Calendar className="h-4 w-4 mr-2 text-gray-400" />
                        {formatDate(user.created_at)}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          className="p-1 text-gray-400 hover:text-blue-600"
                          title="编辑"
                        >
                          <Edit className="h-4 w-4" />
                        </button>
                        <button
                          className="p-1 text-gray-400 hover:text-red-600"
                          title="删除"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>

          {filteredUsers.length === 0 && (
            <div className="py-12 text-center text-gray-500">暂无用户数据</div>
          )}

          {/* Pagination */}
          <div className="px-6 py-4 border-t flex items-center justify-between">
            <div className="text-sm text-gray-500">
              共 {filteredUsers.length} 个用户
            </div>
          </div>
        </div>
      </div>

      {/* Create User Modal Placeholder */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">添加用户</h3>
            <p className="text-gray-500 mb-4">功能开发中...</p>
            <button
              onClick={() => setShowCreateModal(false)}
              className="w-full py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
            >
              关闭
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default UsersPage;
