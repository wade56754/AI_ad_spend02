'use client';

/**
 * Profile Page Component
 *
 * Route: /profile
 * Purpose: Display and manage user profile information
 */

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useAuth } from '@/features/auth';
import {
  User,
  Mail,
  Phone,
  Building,
  Calendar,
  Clock,
  Shield,
  Edit,
  Save,
  X,
  Camera,
  Activity
} from 'lucide-react';

// Mock activity data
const mockActivities = [
  { id: 1, action: '登录系统', resource: '系统', created_at: '2024-12-21 10:30:00', ip_address: '192.168.1.100' },
  { id: 2, action: '查看日报', resource: '日报 #1234', created_at: '2024-12-21 10:25:00', ip_address: '192.168.1.100' },
  { id: 3, action: '审批充值', resource: '充值申请 #5678', created_at: '2024-12-21 10:20:00', ip_address: '192.168.1.100' },
  { id: 4, action: '导出报表', resource: '月度报表', created_at: '2024-12-21 10:15:00', ip_address: '192.168.1.100' },
  { id: 5, action: '修改设置', resource: '通知设置', created_at: '2024-12-21 10:10:00', ip_address: '192.168.1.100' },
];

/**
 * 角色标签 (MASTER.md v4.6 §2.4)
 */
const roleLabels: Record<string, string> = {
  ceo: '老板',
  project_owner: '项目负责人',
  finance: '财务',
  pitcher: '投手',
  account_manager: '户管',
  admin: '管理员',
  // 技术层别名
  media_buyer: '投手',
};

export function ProfilePage() {
  const { user } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [formData, setFormData] = useState({
    name: user?.full_name || user?.username || user?.email?.split('@')[0] || '',
    phone: '',
    department: '',
  });

  const handleSave = () => {
    setIsSaving(true);
    setTimeout(() => {
      setIsSaving(false);
      setIsEditing(false);
    }, 1000);
  };

  const handleCancel = () => {
    setFormData({
      name: user?.full_name || user?.username || user?.email?.split('@')[0] || '',
      phone: '',
      department: '',
    });
    setIsEditing(false);
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-blue-100">
            <User className="h-6 w-6 text-blue-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">个人中心</h1>
            <p className="text-sm text-gray-500">查看和管理您的个人信息</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-6">
        {/* Profile Card */}
        <div className="col-span-12 lg:col-span-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex flex-col items-center">
                {/* Avatar */}
                <div className="relative">
                  <div className="w-24 h-24 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-3xl font-bold">
                    {(user?.full_name || user?.username || user?.email || 'U')[0].toUpperCase()}
                  </div>
                  <button className="absolute bottom-0 right-0 w-8 h-8 bg-white rounded-full border shadow-sm flex items-center justify-center hover:bg-gray-50">
                    <Camera className="h-4 w-4 text-gray-600" />
                  </button>
                </div>

                {/* Name & Role */}
                <h2 className="mt-4 text-xl font-semibold text-gray-900">
                  {user?.full_name || user?.username || user?.email?.split('@')[0] || '用户'}
                </h2>
                <span className="inline-flex items-center px-3 py-1 mt-2 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                  <Shield className="h-3 w-3 mr-1" />
                  {roleLabels[user?.role || ''] || user?.role || '未知角色'}
                </span>

                {/* Stats */}
                <div className="grid grid-cols-2 gap-4 w-full mt-6 pt-6 border-t">
                  <div className="text-center">
                    <p className="text-2xl font-bold text-gray-900">156</p>
                    <p className="text-sm text-gray-500">今日操作</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-gray-900">30</p>
                    <p className="text-sm text-gray-500">活跃天数</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Profile Details */}
        <div className="col-span-12 lg:col-span-8">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>基本信息</CardTitle>
                  <CardDescription>管理您的账户详细信息</CardDescription>
                </div>
                {!isEditing ? (
                  <Button variant="outline" onClick={() => setIsEditing(true)}>
                    <Edit className="h-4 w-4 mr-2" />
                    编辑
                  </Button>
                ) : (
                  <div className="flex gap-2">
                    <Button variant="outline" onClick={handleCancel}>
                      <X className="h-4 w-4 mr-2" />
                      取消
                    </Button>
                    <Button onClick={handleSave} disabled={isSaving}>
                      <Save className="h-4 w-4 mr-2" />
                      {isSaving ? '保存中...' : '保存'}
                    </Button>
                  </div>
                )}
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {/* Email - Read Only */}
                <div className="space-y-2">
                  <Label className="flex items-center gap-2 text-gray-600">
                    <Mail className="h-4 w-4" />
                    邮箱地址
                  </Label>
                  <Input
                    value={user?.email || ''}
                    disabled
                    className="bg-gray-50"
                  />
                  <p className="text-xs text-gray-500">邮箱地址不可修改</p>
                </div>

                {/* Name */}
                <div className="space-y-2">
                  <Label className="flex items-center gap-2 text-gray-600">
                    <User className="h-4 w-4" />
                    显示名称
                  </Label>
                  <Input
                    value={formData.name}
                    onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                    disabled={!isEditing}
                    className={!isEditing ? 'bg-gray-50' : ''}
                  />
                </div>

                {/* Phone */}
                <div className="space-y-2">
                  <Label className="flex items-center gap-2 text-gray-600">
                    <Phone className="h-4 w-4" />
                    手机号码
                  </Label>
                  <Input
                    value={formData.phone}
                    onChange={(e) => setFormData(prev => ({ ...prev, phone: e.target.value }))}
                    disabled={!isEditing}
                    placeholder="请输入手机号码"
                    className={!isEditing ? 'bg-gray-50' : ''}
                  />
                </div>

                {/* Department */}
                <div className="space-y-2">
                  <Label className="flex items-center gap-2 text-gray-600">
                    <Building className="h-4 w-4" />
                    所属部门
                  </Label>
                  <Input
                    value={formData.department}
                    onChange={(e) => setFormData(prev => ({ ...prev, department: e.target.value }))}
                    disabled={!isEditing}
                    placeholder="请输入所属部门"
                    className={!isEditing ? 'bg-gray-50' : ''}
                  />
                </div>

                {/* Role - Read Only */}
                <div className="space-y-2">
                  <Label className="flex items-center gap-2 text-gray-600">
                    <Shield className="h-4 w-4" />
                    账户角色
                  </Label>
                  <Input
                    value={roleLabels[user?.role || ''] || user?.role || '未知角色'}
                    disabled
                    className="bg-gray-50"
                  />
                  <p className="text-xs text-gray-500">角色由管理员分配</p>
                </div>

                {/* Created At */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label className="flex items-center gap-2 text-gray-600">
                      <Calendar className="h-4 w-4" />
                      注册时间
                    </Label>
                    <Input
                      value="2024-01-15 09:30:00"
                      disabled
                      className="bg-gray-50"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="flex items-center gap-2 text-gray-600">
                      <Clock className="h-4 w-4" />
                      最后登录
                    </Label>
                    <Input
                      value="2024-12-21 10:30:00"
                      disabled
                      className="bg-gray-50"
                    />
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Recent Activity */}
        <div className="col-span-12">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5" />
                最近活动
              </CardTitle>
              <CardDescription>您最近的系统操作记录</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-3 px-4 font-medium text-gray-600">时间</th>
                      <th className="text-left py-3 px-4 font-medium text-gray-600">操作</th>
                      <th className="text-left py-3 px-4 font-medium text-gray-600">资源</th>
                      <th className="text-left py-3 px-4 font-medium text-gray-600">IP 地址</th>
                    </tr>
                  </thead>
                  <tbody>
                    {mockActivities.map((activity) => (
                      <tr key={activity.id} className="border-b hover:bg-gray-50">
                        <td className="py-3 px-4 text-sm text-gray-600">
                          <div className="flex items-center gap-2">
                            <Clock className="h-4 w-4" />
                            {activity.created_at}
                          </div>
                        </td>
                        <td className="py-3 px-4 text-sm font-medium text-gray-900">
                          {activity.action}
                        </td>
                        <td className="py-3 px-4 text-sm text-gray-600">
                          {activity.resource}
                        </td>
                        <td className="py-3 px-4 text-sm text-gray-500">
                          {activity.ip_address}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

export default ProfilePage;
