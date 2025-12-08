/**
 * SettingsPage Component
 *
 * 系统设置页面
 */

'use client';

import React, { useState } from 'react';
import {
  Settings,
  User,
  Bell,
  Shield,
  Sliders,
  Save,
  Moon,
  Sun,
  Monitor,
  Lock,
  Mail,
  Globe,
  Clock,
} from 'lucide-react';
import { SETTINGS_SECTIONS } from '../types';

type SettingsTab = 'profile' | 'preferences' | 'notifications' | 'security' | 'system';

export function SettingsPage() {
  const [activeTab, setActiveTab] = useState<SettingsTab>('profile');
  const [isSaving, setIsSaving] = useState(false);

  // Mock user data
  const [profile, setProfile] = useState({
    username: 'admin',
    email: 'admin@example.com',
    full_name: '系统管理员',
  });

  const [preferences, setPreferences] = useState({
    theme: 'system' as 'light' | 'dark' | 'system',
    language: 'zh-CN',
    timezone: 'Asia/Shanghai',
    date_format: 'YYYY-MM-DD',
    sidebar_collapsed: false,
  });

  const [notifications, setNotifications] = useState({
    email_notifications: true,
    daily_report_reminder: true,
    reconciliation_alerts: true,
    low_balance_warning: true,
    low_balance_threshold: 10000,
  });

  const handleSave = async () => {
    setIsSaving(true);
    await new Promise((resolve) => setTimeout(resolve, 1000));
    setIsSaving(false);
    alert('设置已保存');
  };

  const renderTabIcon = (id: string) => {
    switch (id) {
      case 'profile':
        return <User className="h-5 w-5" />;
      case 'preferences':
        return <Sliders className="h-5 w-5" />;
      case 'notifications':
        return <Bell className="h-5 w-5" />;
      case 'security':
        return <Shield className="h-5 w-5" />;
      case 'system':
        return <Settings className="h-5 w-5" />;
      default:
        return <Settings className="h-5 w-5" />;
    }
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'profile':
        return (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                用户名
              </label>
              <input
                type="text"
                value={profile.username}
                onChange={(e) => setProfile({ ...profile, username: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                邮箱
              </label>
              <input
                type="email"
                value={profile.email}
                onChange={(e) => setProfile({ ...profile, email: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                全名
              </label>
              <input
                type="text"
                value={profile.full_name}
                onChange={(e) => setProfile({ ...profile, full_name: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        );

      case 'preferences':
        return (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                主题
              </label>
              <div className="flex gap-4">
                {[
                  { value: 'light', label: '浅色', icon: Sun },
                  { value: 'dark', label: '深色', icon: Moon },
                  { value: 'system', label: '跟随系统', icon: Monitor },
                ].map((option) => (
                  <button
                    key={option.value}
                    onClick={() =>
                      setPreferences({
                        ...preferences,
                        theme: option.value as 'light' | 'dark' | 'system',
                      })
                    }
                    className={`flex items-center gap-2 px-4 py-3 rounded-lg border ${
                      preferences.theme === option.value
                        ? 'border-blue-500 bg-blue-50 text-blue-700'
                        : 'border-gray-300 text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    <option.icon className="h-5 w-5" />
                    {option.label}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <div className="flex items-center gap-2">
                  <Globe className="h-4 w-4" />
                  语言
                </div>
              </label>
              <select
                value={preferences.language}
                onChange={(e) =>
                  setPreferences({ ...preferences, language: e.target.value })
                }
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="zh-CN">简体中文</option>
                <option value="en-US">English</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4" />
                  时区
                </div>
              </label>
              <select
                value={preferences.timezone}
                onChange={(e) =>
                  setPreferences({ ...preferences, timezone: e.target.value })
                }
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="Asia/Shanghai">中国标准时间 (UTC+8)</option>
                <option value="Asia/Hong_Kong">香港时间 (UTC+8)</option>
                <option value="UTC">协调世界时 (UTC)</option>
              </select>
            </div>
          </div>
        );

      case 'notifications':
        return (
          <div className="space-y-6">
            {[
              {
                key: 'email_notifications',
                label: '邮件通知',
                description: '通过邮件接收系统通知',
              },
              {
                key: 'daily_report_reminder',
                label: '日报提醒',
                description: '每日提醒填写日报',
              },
              {
                key: 'reconciliation_alerts',
                label: '对账提醒',
                description: '对账差异和待处理提醒',
              },
              {
                key: 'low_balance_warning',
                label: '余额预警',
                description: '账户余额低于阈值时提醒',
              },
            ].map((item) => (
              <div
                key={item.key}
                className="flex items-center justify-between py-4 border-b"
              >
                <div>
                  <div className="text-sm font-medium text-gray-900">{item.label}</div>
                  <div className="text-sm text-gray-500">{item.description}</div>
                </div>
                <button
                  onClick={() =>
                    setNotifications({
                      ...notifications,
                      [item.key]: !notifications[item.key as keyof typeof notifications],
                    })
                  }
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    notifications[item.key as keyof typeof notifications]
                      ? 'bg-blue-600'
                      : 'bg-gray-200'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      notifications[item.key as keyof typeof notifications]
                        ? 'translate-x-6'
                        : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>
            ))}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                余额预警阈值
              </label>
              <div className="flex items-center gap-2">
                <span className="text-gray-500">¥</span>
                <input
                  type="number"
                  value={notifications.low_balance_threshold}
                  onChange={(e) =>
                    setNotifications({
                      ...notifications,
                      low_balance_threshold: parseInt(e.target.value) || 0,
                    })
                  }
                  className="w-40 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>
        );

      case 'security':
        return (
          <div className="space-y-6">
            <div className="p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3 mb-3">
                <Lock className="h-5 w-5 text-gray-600" />
                <span className="font-medium text-gray-900">修改密码</span>
              </div>
              <div className="space-y-4">
                <input
                  type="password"
                  placeholder="当前密码"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
                <input
                  type="password"
                  placeholder="新密码"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
                <input
                  type="password"
                  placeholder="确认新密码"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
                <button className="px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-900">
                  更新密码
                </button>
              </div>
            </div>

            <div className="p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-3 mb-1">
                    <Shield className="h-5 w-5 text-gray-600" />
                    <span className="font-medium text-gray-900">两步验证</span>
                  </div>
                  <p className="text-sm text-gray-500">
                    启用两步验证以增强账户安全性
                  </p>
                </div>
                <button className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-100">
                  设置
                </button>
              </div>
            </div>

            <div className="p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-3 mb-1">
                    <Mail className="h-5 w-5 text-gray-600" />
                    <span className="font-medium text-gray-900">登录设备</span>
                  </div>
                  <p className="text-sm text-gray-500">查看和管理已登录的设备</p>
                </div>
                <button className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-100">
                  查看
                </button>
              </div>
            </div>
          </div>
        );

      case 'system':
        return (
          <div className="space-y-6">
            <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-sm text-yellow-700">
                以下设置仅管理员可修改，更改后将影响所有用户。
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                站点名称
              </label>
              <input
                type="text"
                defaultValue="AI 广告投放系统"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                数据保留天数
              </label>
              <input
                type="number"
                defaultValue={365}
                className="w-40 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                会话超时时间（分钟）
              </label>
              <input
                type="number"
                defaultValue={60}
                className="w-40 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center gap-3">
            <Settings className="h-8 w-8 text-gray-600" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900">系统设置</h1>
              <p className="text-sm text-gray-500">管理您的账户和系统配置</p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex gap-8">
          {/* Sidebar */}
          <div className="w-64 flex-shrink-0">
            <nav className="bg-white rounded-lg shadow p-4 space-y-1">
              {SETTINGS_SECTIONS.map((section) => (
                <button
                  key={section.id}
                  onClick={() => setActiveTab(section.id as SettingsTab)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-left transition-colors ${
                    activeTab === section.id
                      ? 'bg-blue-50 text-blue-700'
                      : 'text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  {renderTabIcon(section.id)}
                  <div>
                    <div className="text-sm font-medium">{section.title}</div>
                    <div className="text-xs text-gray-500">{section.description}</div>
                  </div>
                </button>
              ))}
            </nav>
          </div>

          {/* Content */}
          <div className="flex-1">
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-6">
                {SETTINGS_SECTIONS.find((s) => s.id === activeTab)?.title}
              </h2>

              {renderContent()}

              <div className="mt-8 pt-6 border-t flex justify-end">
                <button
                  onClick={handleSave}
                  disabled={isSaving}
                  className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {isSaving ? (
                    <>
                      <div className="h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      保存中...
                    </>
                  ) : (
                    <>
                      <Save className="h-4 w-4" />
                      保存设置
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default SettingsPage;
