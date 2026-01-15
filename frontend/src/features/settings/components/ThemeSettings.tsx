/**
 * ThemeSettings Component
 *
 * Theme selection (light/dark/system) and display preferences
 * Using shadcn/ui components for consistent styling
 */

'use client';

import React, { useState, useEffect } from 'react';
import { Sun, Moon, Monitor, Globe, Clock, LayoutGrid, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import { Switch } from '@/components/ui/switch';

// ============================================================
// Types
// ============================================================

interface ThemeSettingsProps {
  onChange?: () => void;
}

type ThemeMode = 'light' | 'dark' | 'system';

interface PreferencesState {
  theme: ThemeMode;
  language: string;
  timezone: string;
  date_format: string;
  compact_mode: boolean;
}

interface ThemeOption {
  value: ThemeMode;
  label: string;
  description: string;
  icon: React.ReactNode;
}

// ============================================================
// Constants
// ============================================================

const THEME_OPTIONS: ThemeOption[] = [
  {
    value: 'light',
    label: '浅色模式',
    description: '明亮的界面，适合白天使用',
    icon: <Sun className="h-5 w-5" />,
  },
  {
    value: 'dark',
    label: '深色模式',
    description: '深色界面，保护眼睛',
    icon: <Moon className="h-5 w-5" />,
  },
  {
    value: 'system',
    label: '跟随系统',
    description: '自动匹配系统主题设置',
    icon: <Monitor className="h-5 w-5" />,
  },
];

const LANGUAGES = [
  { value: 'zh-CN', label: '简体中文' },
  { value: 'zh-TW', label: '繁體中文' },
  { value: 'en-US', label: 'English' },
];

const TIMEZONES = [
  { value: 'Asia/Shanghai', label: '中国标准时间 (UTC+8)' },
  { value: 'Asia/Hong_Kong', label: '香港时间 (UTC+8)' },
  { value: 'Asia/Tokyo', label: '东京时间 (UTC+9)' },
  { value: 'UTC', label: '协调世界时 (UTC)' },
];

const DATE_FORMATS = [
  { value: 'YYYY-MM-DD', label: '2024-01-15' },
  { value: 'DD/MM/YYYY', label: '15/01/2024' },
  { value: 'MM/DD/YYYY', label: '01/15/2024' },
  { value: 'YYYY年MM月DD日', label: '2024年01月15日' },
];

// ============================================================
// Component
// ============================================================

export function ThemeSettings({ onChange }: ThemeSettingsProps) {
  const [preferences, setPreferences] = useState<PreferencesState>({
    theme: 'system',
    language: 'zh-CN',
    timezone: 'Asia/Shanghai',
    date_format: 'YYYY-MM-DD',
    compact_mode: false,
  });

  // Apply theme to document
  useEffect(() => {
    const root = document.documentElement;

    if (preferences.theme === 'system') {
      // Check system preference
      const systemDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      root.classList.toggle('dark', systemDark);
    } else {
      root.classList.toggle('dark', preferences.theme === 'dark');
    }
  }, [preferences.theme]);

  // Handle theme change
  const handleThemeChange = (theme: ThemeMode) => {
    setPreferences((prev) => ({ ...prev, theme }));
    onChange?.();
  };

  // Handle preference change
  const handlePreferenceChange = (key: keyof PreferencesState, value: string | boolean) => {
    setPreferences((prev) => ({ ...prev, [key]: value }));
    onChange?.();
  };

  return (
    <div className="space-y-8">
      {/* Theme Selection */}
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <Sun className="h-4 w-4 text-primary" />
          <h3 className="text-sm font-semibold">主题</h3>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          {THEME_OPTIONS.map((option) => (
            <Button
              key={option.value}
              type="button"
              variant="outline"
              onClick={() => handleThemeChange(option.value)}
              className={`
                relative h-auto w-full whitespace-normal items-start justify-start border-2 p-4 text-left transition-all
                hover:border-primary/50
                ${
                  preferences.theme === option.value
                    ? 'border-primary bg-primary/5'
                    : 'border-border'
                }
              `}
            >
              {preferences.theme === option.value && (
                <div className="absolute top-2 right-2">
                  <Check className="h-4 w-4 text-primary" />
                </div>
              )}
              <div
                className={`
                mb-3 p-2 rounded-md w-fit
                ${
                  preferences.theme === option.value
                    ? 'bg-primary/10 text-primary'
                    : 'bg-muted text-muted-foreground'
                }
              `}
              >
                {option.icon}
              </div>
              <p className="font-medium text-sm">{option.label}</p>
              <p className="text-xs text-muted-foreground mt-1">{option.description}</p>
            </Button>
          ))}
        </div>
      </div>

      <Separator />

      {/* Language & Region */}
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <Globe className="h-4 w-4 text-primary" />
          <h3 className="text-sm font-semibold">语言和区域</h3>
        </div>

        <div className="grid gap-6 max-w-md">
          {/* Language */}
          <div className="grid gap-2">
            <Label htmlFor="language" className="flex items-center gap-2">
              <Globe className="h-4 w-4 text-muted-foreground" />
              显示语言
            </Label>
            <Select
              value={preferences.language}
              onValueChange={(value) => handlePreferenceChange('language', value)}
            >
              <SelectTrigger id="language">
                <SelectValue placeholder="选择语言" />
              </SelectTrigger>
              <SelectContent>
                {LANGUAGES.map((lang) => (
                  <SelectItem key={lang.value} value={lang.value}>
                    {lang.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Timezone */}
          <div className="grid gap-2">
            <Label htmlFor="timezone" className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-muted-foreground" />
              时区
            </Label>
            <Select
              value={preferences.timezone}
              onValueChange={(value) => handlePreferenceChange('timezone', value)}
            >
              <SelectTrigger id="timezone">
                <SelectValue placeholder="选择时区" />
              </SelectTrigger>
              <SelectContent>
                {TIMEZONES.map((tz) => (
                  <SelectItem key={tz.value} value={tz.value}>
                    {tz.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Date Format */}
          <div className="grid gap-2">
            <Label htmlFor="date_format" className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-muted-foreground" />
              日期格式
            </Label>
            <Select
              value={preferences.date_format}
              onValueChange={(value) => handlePreferenceChange('date_format', value)}
            >
              <SelectTrigger id="date_format">
                <SelectValue placeholder="选择日期格式" />
              </SelectTrigger>
              <SelectContent>
                {DATE_FORMATS.map((fmt) => (
                  <SelectItem key={fmt.value} value={fmt.value}>
                    {fmt.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>

      <Separator />

      {/* Display Options */}
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <LayoutGrid className="h-4 w-4 text-primary" />
          <h3 className="text-sm font-semibold">显示选项</h3>
        </div>

        <div className="max-w-md space-y-4">
          {/* Compact Mode */}
          <div className="flex items-center justify-between p-4 border rounded-lg">
            <div className="space-y-1">
              <Label htmlFor="compact_mode" className="text-sm font-medium">
                紧凑模式
              </Label>
              <p className="text-xs text-muted-foreground">减少界面间距，在同一屏幕显示更多内容</p>
            </div>
            <Switch
              id="compact_mode"
              checked={preferences.compact_mode}
              onCheckedChange={(checked) => handlePreferenceChange('compact_mode', checked)}
            />
          </div>

          {/* Preview */}
          <div className="p-4 bg-muted/50 rounded-lg">
            <p className="text-xs text-muted-foreground mb-2">预览</p>
            <div
              className={`
              border rounded-md bg-background p-3
              ${preferences.compact_mode ? 'space-y-2' : 'space-y-4'}
            `}
            >
              <div
                className={`h-2 bg-muted rounded ${preferences.compact_mode ? 'w-3/4' : 'w-full'}`}
              />
              <div
                className={`h-2 bg-muted rounded ${preferences.compact_mode ? 'w-1/2' : 'w-3/4'}`}
              />
              <div
                className={`h-2 bg-muted rounded ${preferences.compact_mode ? 'w-2/3' : 'w-5/6'}`}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ThemeSettings;
