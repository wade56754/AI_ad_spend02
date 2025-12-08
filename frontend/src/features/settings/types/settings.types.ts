/**
 * Settings Types
 */

export interface SystemSettings {
  // 通用设置
  site_name: string;
  timezone: string;
  language: string;
  currency: string;

  // 通知设置
  email_notifications: boolean;
  daily_report_reminder: boolean;
  reconciliation_alerts: boolean;
  low_balance_warning: boolean;
  low_balance_threshold: number;

  // 数据设置
  data_retention_days: number;
  auto_archive_completed: boolean;
  default_page_size: number;

  // 安全设置
  session_timeout_minutes: number;
  require_2fa: boolean;
  password_expiry_days: number;
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'system';
  sidebar_collapsed: boolean;
  dashboard_layout: 'default' | 'compact';
  date_format: string;
  number_format: string;
  notifications_enabled: boolean;
  sound_enabled: boolean;
}

export interface SettingsSection {
  id: string;
  title: string;
  description: string;
  icon: string;
}

export const SETTINGS_SECTIONS: SettingsSection[] = [
  {
    id: 'profile',
    title: '个人资料',
    description: '管理您的账户信息和密码',
    icon: 'user',
  },
  {
    id: 'preferences',
    title: '偏好设置',
    description: '自定义界面和显示选项',
    icon: 'sliders',
  },
  {
    id: 'notifications',
    title: '通知设置',
    description: '配置系统通知和提醒',
    icon: 'bell',
  },
  {
    id: 'security',
    title: '安全设置',
    description: '密码和两步验证',
    icon: 'shield',
  },
  {
    id: 'system',
    title: '系统配置',
    description: '全局系统参数（仅管理员）',
    icon: 'settings',
  },
];
