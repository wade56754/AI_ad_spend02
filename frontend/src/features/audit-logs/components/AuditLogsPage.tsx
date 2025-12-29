'use client';

/**
 * Audit Logs Page Component
 *
 * Route: /audit-logs
 * Purpose: Display system audit logs and activity history
 */

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Search,
  FileText,
  User,
  Clock,
  Activity,
  Shield,
  Filter,
  Download,
  RefreshCw,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';

// Mock data
const mockLogs = [
  {
    id: 1,
    user_name: 'admin@example.com',
    user_role: 'admin',
    action: 'LOGIN',
    resource_type: 'auth',
    resource_name: '系统登录',
    ip_address: '192.168.1.100',
    created_at: '2024-12-21 10:30:25',
  },
  {
    id: 2,
    user_name: 'finance@example.com',
    user_role: 'finance',
    action: 'CREATE',
    resource_type: 'topup',
    resource_name: '充值申请 #1234',
    ip_address: '192.168.1.101',
    created_at: '2024-12-21 10:25:18',
  },
  {
    id: 3,
    user_name: 'admin@example.com',
    user_role: 'admin',
    action: 'UPDATE',
    resource_type: 'user',
    resource_name: '用户 finance@example.com',
    ip_address: '192.168.1.100',
    created_at: '2024-12-21 10:20:00',
  },
  {
    id: 4,
    user_name: 'owner@example.com',
    user_role: 'project_owner',
    action: 'APPROVE',
    resource_type: 'daily_report',
    resource_name: '日报 #5678',
    ip_address: '192.168.1.102',
    created_at: '2024-12-21 10:15:33',
  },
  {
    id: 5,
    user_name: 'admin@example.com',
    user_role: 'admin',
    action: 'DELETE',
    resource_type: 'project',
    resource_name: '测试项目',
    ip_address: '192.168.1.100',
    created_at: '2024-12-21 10:10:00',
  },
];

const actionColors: Record<string, string> = {
  LOGIN: 'bg-blue-100 text-blue-800',
  LOGOUT: 'bg-gray-100 text-gray-800',
  CREATE: 'bg-green-100 text-green-800',
  UPDATE: 'bg-yellow-100 text-yellow-800',
  DELETE: 'bg-red-100 text-red-800',
  APPROVE: 'bg-purple-100 text-purple-800',
  REJECT: 'bg-orange-100 text-orange-800',
};

const actionLabels: Record<string, string> = {
  LOGIN: '登录',
  LOGOUT: '登出',
  CREATE: '创建',
  UPDATE: '更新',
  DELETE: '删除',
  APPROVE: '审批',
  REJECT: '拒绝',
};

export function AuditLogsPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);

  const handleRefresh = () => {
    setIsLoading(true);
    setTimeout(() => setIsLoading(false), 1000);
  };

  const filteredLogs = mockLogs.filter(log =>
    log.user_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    log.resource_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    log.action.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-100">
            <Shield className="h-6 w-6 text-indigo-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">审计日志</h1>
            <p className="text-sm text-gray-500">查看系统操作记录和安全审计</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline">
            <Download className="h-4 w-4 mr-2" />
            导出
          </Button>
          <Button variant="outline" onClick={handleRefresh} disabled={isLoading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            刷新
          </Button>
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">今日操作</p>
                <p className="text-2xl font-bold text-gray-900">156</p>
              </div>
              <Activity className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">活跃用户</p>
                <p className="text-2xl font-bold text-gray-900">12</p>
              </div>
              <User className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">本周日志</p>
                <p className="text-2xl font-bold text-gray-900">1,234</p>
              </div>
              <FileText className="h-8 w-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">安全事件</p>
                <p className="text-2xl font-bold text-gray-900">0</p>
              </div>
              <Shield className="h-8 w-8 text-red-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters & Search */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-wrap items-center gap-4">
            <div className="relative flex-1 min-w-[200px]">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
              <Input
                placeholder="搜索用户、操作或资源..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <Button variant="outline">
              <Filter className="h-4 w-4 mr-2" />
              筛选
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Logs Table */}
      <Card>
        <CardHeader>
          <CardTitle>操作记录</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-4 font-medium text-gray-600">时间</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">用户</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">操作</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">资源</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">IP地址</th>
                </tr>
              </thead>
              <tbody>
                {filteredLogs.map((log) => (
                  <tr key={log.id} className="border-b hover:bg-gray-50">
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2 text-sm text-gray-600">
                        <Clock className="h-4 w-4" />
                        {log.created_at}
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <div>
                        <p className="font-medium text-gray-900">{log.user_name}</p>
                        <p className="text-xs text-gray-500">{log.user_role}</p>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${actionColors[log.action] || 'bg-gray-100 text-gray-800'}`}>
                        {actionLabels[log.action] || log.action}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <p className="text-sm text-gray-900">{log.resource_name}</p>
                      <p className="text-xs text-gray-500">{log.resource_type}</p>
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-600">
                      {log.ip_address}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between mt-4 pt-4 border-t">
            <p className="text-sm text-gray-500">
              显示 1-5 条，共 156 条记录
            </p>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={currentPage === 1}
                onClick={() => setCurrentPage(p => p - 1)}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <span className="text-sm text-gray-600">第 {currentPage} 页</span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(p => p + 1)}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default AuditLogsPage;
