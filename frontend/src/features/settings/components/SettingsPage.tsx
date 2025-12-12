/**
 * SettingsPage Component
 *
 * Main settings page with tabbed navigation
 * Uses shadcn/ui components following project patterns
 *
 * Layout: Sidebar navigation + Content area
 * Sub-components: ProfileSettings, NotificationSettings, SecuritySettings, ThemeSettings
 */

'use client';

import React, { useState, useCallback } from 'react';
import {
  Settings,
  User,
  Bell,
  Shield,
  Sliders,
  Save,
  Loader2,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useAuth } from '@/features/auth';

import { ProfileSettings } from './ProfileSettings';
import { NotificationSettings } from './NotificationSettings';
import { SecuritySettings } from './SecuritySettings';
import { ThemeSettings } from './ThemeSettings';

// ============================================================
// Types
// ============================================================

export type SettingsTab = 'profile' | 'preferences' | 'notifications' | 'security';

interface SettingsSection {
  id: SettingsTab;
  title: string;
  description: string;
  icon: React.ReactNode;
}

// ============================================================
// Constants
// ============================================================

const SETTINGS_TABS: SettingsSection[] = [
  {
    id: 'profile',
    title: '个人资料',
    description: '管理您的账户信息',
    icon: <User className="h-4 w-4" />,
  },
  {
    id: 'preferences',
    title: '偏好设置',
    description: '主题和显示选项',
    icon: <Sliders className="h-4 w-4" />,
  },
  {
    id: 'notifications',
    title: '通知设置',
    description: '配置系统通知',
    icon: <Bell className="h-4 w-4" />,
  },
  {
    id: 'security',
    title: '安全设置',
    description: '密码和会话管理',
    icon: <Shield className="h-4 w-4" />,
  },
];

// ============================================================
// Main Component
// ============================================================

export function SettingsPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<SettingsTab>('profile');
  const [isSaving, setIsSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  // Handle save - would integrate with API in production
  const handleSave = useCallback(async () => {
    setIsSaving(true);
    try {
      // TODO: Replace with actual API call
      await new Promise((resolve) => setTimeout(resolve, 1000));
      setHasChanges(false);
      // Could show toast notification here
    } catch (error) {
      console.error('Failed to save settings:', error);
    } finally {
      setIsSaving(false);
    }
  }, []);

  // Mark as changed when any setting is modified
  const handleChange = useCallback(() => {
    setHasChanges(true);
  }, []);

  return (
    <div className="container mx-auto py-6 space-y-6" data-testid="settings-page">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Settings className="h-8 w-8 text-muted-foreground" />
          <div>
            <h1 className="text-2xl font-bold">系统设置</h1>
            <p className="text-muted-foreground">管理您的账户和偏好设置</p>
          </div>
        </div>
        <Button
          onClick={handleSave}
          disabled={isSaving || !hasChanges}
        >
          {isSaving ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              保存中...
            </>
          ) : (
            <>
              <Save className="mr-2 h-4 w-4" />
              保存设置
            </>
          )}
        </Button>
      </div>

      {/* Settings Content */}
      <Tabs
        value={activeTab}
        onValueChange={(v) => setActiveTab(v as SettingsTab)}
        className="space-y-6"
      >
        {/* Tab Navigation */}
        <TabsList className="grid w-full grid-cols-4 lg:w-auto lg:inline-flex">
          {SETTINGS_TABS.map((tab) => (
            <TabsTrigger
              key={tab.id}
              value={tab.id}
              className="flex items-center gap-2"
            >
              {tab.icon}
              <span className="hidden sm:inline">{tab.title}</span>
            </TabsTrigger>
          ))}
        </TabsList>

        {/* Profile Settings */}
        <TabsContent value="profile" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="h-5 w-5" />
                个人资料
              </CardTitle>
              <CardDescription>
                查看和更新您的个人信息
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ProfileSettings
                user={user}
                onChange={handleChange}
              />
            </CardContent>
          </Card>
        </TabsContent>

        {/* Theme/Preferences Settings */}
        <TabsContent value="preferences" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sliders className="h-5 w-5" />
                偏好设置
              </CardTitle>
              <CardDescription>
                自定义界面主题和显示选项
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ThemeSettings onChange={handleChange} />
            </CardContent>
          </Card>
        </TabsContent>

        {/* Notification Settings */}
        <TabsContent value="notifications" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bell className="h-5 w-5" />
                通知设置
              </CardTitle>
              <CardDescription>
                配置邮件通知和系统提醒
              </CardDescription>
            </CardHeader>
            <CardContent>
              <NotificationSettings onChange={handleChange} />
            </CardContent>
          </Card>
        </TabsContent>

        {/* Security Settings */}
        <TabsContent value="security" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="h-5 w-5" />
                安全设置
              </CardTitle>
              <CardDescription>
                管理密码和登录会话
              </CardDescription>
            </CardHeader>
            <CardContent>
              <SecuritySettings />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default SettingsPage;
