/**
 * NotificationSettings Component
 *
 * Configures email and system notification preferences
 * Using shadcn/ui Switch components for toggles
 */

'use client';

import React, { useState } from 'react';
import { Mail, Bell, AlertTriangle, FileText, Wallet } from 'lucide-react';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Separator } from '@/components/ui/separator';

// ============================================================
// Types
// ============================================================

interface NotificationSettingsProps {
  onChange?: () => void;
}

interface NotificationState {
  // Email Notifications
  email_enabled: boolean;
  email_daily_report: boolean;
  email_weekly_summary: boolean;
  
  // System Notifications
  system_enabled: boolean;
  system_reconciliation_alerts: boolean;
  system_topup_status: boolean;
  system_low_balance: boolean;
  
  // Thresholds
  low_balance_threshold: number;
}

interface NotificationItemProps {
  id: string;
  icon: React.ReactNode;
  title: string;
  description: string;
  checked: boolean;
  onCheckedChange: (checked: boolean) => void;
  disabled?: boolean;
}

// ============================================================
// Sub-components
// ============================================================

function NotificationItem({
  id,
  icon,
  title,
  description,
  checked,
  onCheckedChange,
  disabled = false,
}: NotificationItemProps) {
  return (
    <div className="flex items-center justify-between py-4">
      <div className="flex items-start gap-3">
        <div className="mt-0.5 text-muted-foreground">{icon}</div>
        <div className="space-y-1">
          <Label
            htmlFor={id}
            className={`text-sm font-medium ${disabled ? 'text-muted-foreground' : ''}`}
          >
            {title}
          </Label>
          <p className="text-xs text-muted-foreground">{description}</p>
        </div>
      </div>
      <Switch
        id={id}
        checked={checked}
        onCheckedChange={onCheckedChange}
        disabled={disabled}
      />
    </div>
  );
}

// ============================================================
// Main Component
// ============================================================

export function NotificationSettings({ onChange }: NotificationSettingsProps) {
  const [notifications, setNotifications] = useState<NotificationState>({
    // Email defaults
    email_enabled: true,
    email_daily_report: true,
    email_weekly_summary: false,
    
    // System defaults
    system_enabled: true,
    system_reconciliation_alerts: true,
    system_topup_status: true,
    system_low_balance: true,
    
    // Thresholds
    low_balance_threshold: 10000,
  });

  // Generic toggle handler
  const handleToggle = (key: keyof NotificationState, value: boolean) => {
    setNotifications(prev => ({ ...prev, [key]: value }));
    onChange?.();
  };

  // Threshold change handler
  const handleThresholdChange = (value: string) => {
    const numValue = parseInt(value) || 0;
    setNotifications(prev => ({ ...prev, low_balance_threshold: numValue }));
    onChange?.();
  };

  return (
    <div className="space-y-6">
      {/* Email Notifications Section */}
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <Mail className="h-4 w-4 text-primary" />
          <h3 className="text-sm font-semibold">邮件通知</h3>
        </div>
        
        <div className="border rounded-lg divide-y">
          <NotificationItem
            id="email_enabled"
            icon={<Mail className="h-4 w-4" />}
            title="启用邮件通知"
            description="通过邮件接收系统通知和提醒"
            checked={notifications.email_enabled}
            onCheckedChange={(checked) => handleToggle('email_enabled', checked)}
          />
          
          <NotificationItem
            id="email_daily_report"
            icon={<FileText className="h-4 w-4" />}
            title="日报提醒"
            description="每日提醒填写广告日报"
            checked={notifications.email_daily_report}
            onCheckedChange={(checked) => handleToggle('email_daily_report', checked)}
            disabled={!notifications.email_enabled}
          />
          
          <NotificationItem
            id="email_weekly_summary"
            icon={<FileText className="h-4 w-4" />}
            title="周报汇总"
            description="每周发送投放数据汇总邮件"
            checked={notifications.email_weekly_summary}
            onCheckedChange={(checked) => handleToggle('email_weekly_summary', checked)}
            disabled={!notifications.email_enabled}
          />
        </div>
      </div>

      <Separator />

      {/* System Notifications Section */}
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <Bell className="h-4 w-4 text-primary" />
          <h3 className="text-sm font-semibold">系统通知</h3>
        </div>
        
        <div className="border rounded-lg divide-y">
          <NotificationItem
            id="system_enabled"
            icon={<Bell className="h-4 w-4" />}
            title="启用系统通知"
            description="在系统内接收实时通知"
            checked={notifications.system_enabled}
            onCheckedChange={(checked) => handleToggle('system_enabled', checked)}
          />
          
          <NotificationItem
            id="system_reconciliation_alerts"
            icon={<AlertTriangle className="h-4 w-4" />}
            title="对账提醒"
            description="对账差异和待处理事项提醒"
            checked={notifications.system_reconciliation_alerts}
            onCheckedChange={(checked) => handleToggle('system_reconciliation_alerts', checked)}
            disabled={!notifications.system_enabled}
          />
          
          <NotificationItem
            id="system_topup_status"
            icon={<Wallet className="h-4 w-4" />}
            title="充值状态通知"
            description="充值申请状态变更时通知"
            checked={notifications.system_topup_status}
            onCheckedChange={(checked) => handleToggle('system_topup_status', checked)}
            disabled={!notifications.system_enabled}
          />
          
          <NotificationItem
            id="system_low_balance"
            icon={<AlertTriangle className="h-4 w-4" />}
            title="余额预警"
            description="账户余额低于阈值时通知"
            checked={notifications.system_low_balance}
            onCheckedChange={(checked) => handleToggle('system_low_balance', checked)}
            disabled={!notifications.system_enabled}
          />
        </div>
      </div>

      <Separator />

      {/* Threshold Settings */}
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-primary" />
          <h3 className="text-sm font-semibold">预警阈值</h3>
        </div>
        
        <div className="grid gap-4 max-w-md">
          <div className="grid gap-2">
            <Label htmlFor="low_balance_threshold">
              余额预警阈值
            </Label>
            <div className="flex items-center gap-2">
              <span className="text-muted-foreground">CNY</span>
              <Input
                id="low_balance_threshold"
                type="number"
                min={0}
                step={1000}
                value={notifications.low_balance_threshold}
                onChange={(e) => handleThresholdChange(e.target.value)}
                className="w-40"
                disabled={!notifications.system_low_balance || !notifications.system_enabled}
              />
            </div>
            <p className="text-xs text-muted-foreground">
              当账户余额低于此金额时，系统将发送预警通知
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default NotificationSettings;
