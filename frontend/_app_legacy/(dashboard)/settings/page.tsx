'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Switch } from '@/components/ui/switch';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Settings,
  Shield,
  Bell,
  Database,
  Mail,
  Users,
  Clock,
  Globe,
  Smartphone,
  CreditCard,
  AlertTriangle,
  CheckCircle,
  Info,
  RefreshCw,
  Download,
  Upload,
  Trash2,
  Plus,
  Edit,
  Copy,
  Eye,
  EyeOff,
} from 'lucide-react';
import { toast } from 'sonner';

interface SystemSettings {
  general: {
    siteName: string;
    siteUrl: string;
    timezone: string;
    language: string;
    dateFormat: string;
    currency: string;
  };
  security: {
    sessionTimeout: number;
    passwordMinLength: number;
    requireTwoFactor: boolean;
    allowSessionPersistence: boolean;
    maxLoginAttempts: number;
    lockoutDuration: number;
  };
  notifications: {
    emailNotifications: boolean;
    smsNotifications: boolean;
    pushNotifications: boolean;
    maintenanceAlerts: boolean;
    securityAlerts: boolean;
    billingAlerts: boolean;
  };
  backup: {
    autoBackup: boolean;
    backupFrequency: string;
    retentionPeriod: number;
    backupLocation: string;
    compressionEnabled: boolean;
  };
}

export default function SettingsPage() {
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState('general');
  const [settings, setSettings] = useState<SystemSettings>({
    general: {
      siteName: 'AI广告代投系统',
      siteUrl: 'https://ai-ads.example.com',
      timezone: 'Asia/Shanghai',
      language: 'zh-CN',
      dateFormat: 'YYYY-MM-DD',
      currency: 'CNY',
    },
    security: {
      sessionTimeout: 24,
      passwordMinLength: 8,
      requireTwoFactor: false,
      allowSessionPersistence: true,
      maxLoginAttempts: 5,
      lockoutDuration: 15,
    },
    notifications: {
      emailNotifications: true,
      smsNotifications: false,
      pushNotifications: true,
      maintenanceAlerts: true,
      securityAlerts: true,
      billingAlerts: true,
    },
    backup: {
      autoBackup: true,
      backupFrequency: 'daily',
      retentionPeriod: 30,
      backupLocation: 'cloud',
      compressionEnabled: true,
    },
  });

  const [showApiKeyDialog, setShowApiKeyDialog] = useState(false);
  const [apiKeys, setApiKeys] = useState([
    { id: '1', name: '生产环境API', key: 'sk_prod_1234567890abcdef', createdAt: '2024-01-01', lastUsed: '2024-01-15' },
    { id: '2', name: '测试环境API', key: 'sk_test_1234567890abcdef', createdAt: '2024-01-05', lastUsed: '2024-01-14' },
  ]);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    setLoading(true);
    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 1000));
      // 设置已通过useState初始化
    } catch (error) {
      console.error('获取设置失败:', error);
      toast.error('获取系统设置失败');
    } finally {
      setLoading(false);
    }
  };

  const saveSettings = async () => {
    setSaving(true);
    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 1000));
      toast.success('设置保存成功');
    } catch (error) {
      console.error('保存设置失败:', error);
      toast.error('保存设置失败');
    } finally {
      setSaving(false);
    }
  };

  const updateSetting = (category: keyof SystemSettings, key: string, value: any) => {
    setSettings(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [key]: value,
      },
    }));
  };

  const handleExportSettings = () => {
    toast.info('正在导出系统设置...');
    // 实际导出逻辑
  };

  const handleImportSettings = () => {
    toast.info('正在导入系统设置...');
    // 实际导入逻辑
  };

  const handleResetSettings = () => {
    if (confirm('确定要重置所有设置为默认值吗？')) {
      toast.success('设置已重置为默认值');
      // 实际重置逻辑
    }
  };

  const createApiKey = async (name: string) => {
    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 1000));

      const newKey = {
        id: Date.now().toString(),
        name,
        key: `sk_${Math.random().toString(36).substring(2, 15)}`,
        createdAt: new Date().toISOString().split('T')[0],
        lastUsed: '-',
      };

      setApiKeys([newKey, ...apiKeys]);
      toast.success('API密钥创建成功');
      setShowApiKeyDialog(false);
    } catch (error) {
      console.error('创建API密钥失败:', error);
      toast.error('创建API密钥失败');
    }
  };

  const deleteApiKey = async (keyId: string) => {
    if (!confirm('确定要删除此API密钥吗？')) return;

    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 500));

      setApiKeys(apiKeys.filter(k => k.id !== keyId));
      toast.success('API密钥删除成功');
    } catch (error) {
      console.error('删除API密钥失败:', error);
      toast.error('删除API密钥失败');
    }
  };

  return (
    <div className="container mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">系统设置</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            配置系统参数、安全策略和功能选项
          </p>
        </div>
        <div className="flex space-x-3">
          <Button variant="outline" onClick={handleImportSettings}>
            <Upload className="mr-2 h-4 w-4" />
            导入设置
          </Button>
          <Button variant="outline" onClick={handleExportSettings}>
            <Download className="mr-2 h-4 w-4" />
            导出设置
          </Button>
          <Button onClick={saveSettings} disabled={saving}>
            {saving ? (
              <>
                <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                保存中...
              </>
            ) : (
              <>
                <CheckCircle className="mr-2 h-4 w-4" />
                保存设置
              </>
            )}
          </Button>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="general">常规设置</TabsTrigger>
          <TabsTrigger value="security">安全设置</TabsTrigger>
          <TabsTrigger value="notifications">通知设置</TabsTrigger>
          <TabsTrigger value="backup">备份设置</TabsTrigger>
          <TabsTrigger value="api">API管理</TabsTrigger>
        </TabsList>

        {/* 常规设置 */}
        <TabsContent value="general">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Settings className="mr-2 h-5 w-5" />
                常规设置
              </CardTitle>
              <CardDescription>
                配置系统的基本参数和显示选项
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <Label htmlFor="siteName">站点名称</Label>
                  <Input
                    id="siteName"
                    value={settings.general.siteName}
                    onChange={(e) => updateSetting('general', 'siteName', e.target.value)}
                  />
                </div>
                <div>
                  <Label htmlFor="siteUrl">站点URL</Label>
                  <Input
                    id="siteUrl"
                    value={settings.general.siteUrl}
                    onChange={(e) => updateSetting('general', 'siteUrl', e.target.value)}
                  />
                </div>
                <div>
                  <Label htmlFor="timezone">时区</Label>
                  <Select
                    value={settings.general.timezone}
                    onValueChange={(value) => updateSetting('general', 'timezone', value)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Asia/Shanghai">Asia/Shanghai</SelectItem>
                      <SelectItem value="Asia/Tokyo">Asia/Tokyo</SelectItem>
                      <SelectItem value="America/New_York">America/New_York</SelectItem>
                      <SelectItem value="Europe/London">Europe/London</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="language">语言</Label>
                  <Select
                    value={settings.general.language}
                    onValueChange={(value) => updateSetting('general', 'language', value)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="zh-CN">简体中文</SelectItem>
                      <SelectItem value="zh-TW">繁体中文</SelectItem>
                      <SelectItem value="en-US">English</SelectItem>
                      <SelectItem value="ja-JP">日本語</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="dateFormat">日期格式</Label>
                  <Select
                    value={settings.general.dateFormat}
                    onValueChange={(value) => updateSetting('general', 'dateFormat', value)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="YYYY-MM-DD">YYYY-MM-DD</SelectItem>
                      <SelectItem value="DD/MM/YYYY">DD/MM/YYYY</SelectItem>
                      <SelectItem value="MM/DD/YYYY">MM/DD/YYYY</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="currency">货币</Label>
                  <Select
                    value={settings.general.currency}
                    onValueChange={(value) => updateSetting('general', 'currency', value)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="CNY">人民币 (CNY)</SelectItem>
                      <SelectItem value="USD">美元 (USD)</SelectItem>
                      <SelectItem value="EUR">欧元 (EUR)</SelectItem>
                      <SelectItem value="JPY">日元 (JPY)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 安全设置 */}
        <TabsContent value="security">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Shield className="mr-2 h-5 w-5" />
                安全设置
              </CardTitle>
              <CardDescription>
                配置用户认证、会话管理和安全策略
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <Label htmlFor="sessionTimeout">会话超时 (小时)</Label>
                  <Input
                    id="sessionTimeout"
                    type="number"
                    value={settings.security.sessionTimeout}
                    onChange={(e) => updateSetting('security', 'sessionTimeout', parseInt(e.target.value))}
                  />
                </div>
                <div>
                  <Label htmlFor="passwordMinLength">密码最小长度</Label>
                  <Input
                    id="passwordMinLength"
                    type="number"
                    value={settings.security.passwordMinLength}
                    onChange={(e) => updateSetting('security', 'passwordMinLength', parseInt(e.target.value))}
                  />
                </div>
                <div>
                  <Label htmlFor="maxLoginAttempts">最大登录尝试次数</Label>
                  <Input
                    id="maxLoginAttempts"
                    type="number"
                    value={settings.security.maxLoginAttempts}
                    onChange={(e) => updateSetting('security', 'maxLoginAttempts', parseInt(e.target.value))}
                  />
                </div>
                <div>
                  <Label htmlFor="lockoutDuration">锁定持续时间 (分钟)</Label>
                  <Input
                    id="lockoutDuration"
                    type="number"
                    value={settings.security.lockoutDuration}
                    onChange={(e) => updateSetting('security', 'lockoutDuration', parseInt(e.target.value))}
                  />
                </div>
              </div>

              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>强制双因素认证</Label>
                    <p className="text-sm text-gray-500">要求所有用户启用双因素认证</p>
                  </div>
                  <Switch
                    checked={settings.security.requireTwoFactor}
                    onCheckedChange={(checked) => updateSetting('security', 'requireTwoFactor', checked)}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>允许会话持久化</Label>
                    <p className="text-sm text-gray-500">允许用户保持登录状态</p>
                  </div>
                  <Switch
                    checked={settings.security.allowSessionPersistence}
                    onCheckedChange={(checked) => updateSetting('security', 'allowSessionPersistence', checked)}
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 通知设置 */}
        <TabsContent value="notifications">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Bell className="mr-2 h-5 w-5" />
                通知设置
              </CardTitle>
              <CardDescription>
                配置系统通知和警报规则
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>邮件通知</Label>
                  <p className="text-sm text-gray-500">通过邮件发送系统通知</p>
                </div>
                <Switch
                  checked={settings.notifications.emailNotifications}
                  onCheckedChange={(checked) => updateSetting('notifications', 'emailNotifications', checked)}
                />
              </div>
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>短信通知</Label>
                  <p className="text-sm text-gray-500">通过短信发送紧急通知</p>
                </div>
                <Switch
                  checked={settings.notifications.smsNotifications}
                  onCheckedChange={(checked) => updateSetting('notifications', 'smsNotifications', checked)}
                />
              </div>
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>推送通知</Label>
                  <p className="text-sm text-gray-500">通过浏览器推送通知</p>
                </div>
                <Switch
                  checked={settings.notifications.pushNotifications}
                  onCheckedChange={(checked) => updateSetting('notifications', 'pushNotifications', checked)}
                />
              </div>
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>维护提醒</Label>
                  <p className="text-sm text-gray-500">系统维护和更新通知</p>
                </div>
                <Switch
                  checked={settings.notifications.maintenanceAlerts}
                  onCheckedChange={(checked) => updateSetting('notifications', 'maintenanceAlerts', checked)}
                />
              </div>
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>安全警报</Label>
                  <p className="text-sm text-gray-500">异常登录和安全事件通知</p>
                </div>
                <Switch
                  checked={settings.notifications.securityAlerts}
                  onCheckedChange={(checked) => updateSetting('notifications', 'securityAlerts', checked)}
                />
              </div>
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>账单提醒</Label>
                  <p className="text-sm text-gray-500">充值和消费相关通知</p>
                </div>
                <Switch
                  checked={settings.notifications.billingAlerts}
                  onCheckedChange={(checked) => updateSetting('notifications', 'billingAlerts', checked)}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 备份设置 */}
        <TabsContent value="backup">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Database className="mr-2 h-5 w-5" />
                备份设置
              </CardTitle>
              <CardDescription>
                配置数据自动备份和恢复策略
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <Label htmlFor="backupFrequency">备份频率</Label>
                  <Select
                    value={settings.backup.backupFrequency}
                    onValueChange={(value) => updateSetting('backup', 'backupFrequency', value)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="hourly">每小时</SelectItem>
                      <SelectItem value="daily">每天</SelectItem>
                      <SelectItem value="weekly">每周</SelectItem>
                      <SelectItem value="monthly">每月</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="retentionPeriod">保留天数</Label>
                  <Input
                    id="retentionPeriod"
                    type="number"
                    value={settings.backup.retentionPeriod}
                    onChange={(e) => updateSetting('backup', 'retentionPeriod', parseInt(e.target.value))}
                  />
                </div>
              </div>

              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>自动备份</Label>
                    <p className="text-sm text-gray-500">启用定时自动备份</p>
                  </div>
                  <Switch
                    checked={settings.backup.autoBackup}
                    onCheckedChange={(checked) => updateSetting('backup', 'autoBackup', checked)}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>压缩备份文件</Label>
                    <p className="text-sm text-gray-500">压缩备份文件以节省存储空间</p>
                  </div>
                  <Switch
                    checked={settings.backup.compressionEnabled}
                    onCheckedChange={(checked) => updateSetting('backup', 'compressionEnabled', checked)}
                  />
                </div>
              </div>

              <div className="pt-4 border-t">
                <h4 className="text-lg font-medium mb-4">备份操作</h4>
                <div className="flex space-x-3">
                  <Button>立即备份</Button>
                  <Button variant="outline">恢复备份</Button>
                  <Button variant="outline">查看备份历史</Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* API管理 */}
        <TabsContent value="api">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <div className="flex items-center">
                  <CreditCard className="mr-2 h-5 w-5" />
                  API管理
                </div>
                <Dialog open={showApiKeyDialog} onOpenChange={setShowApiKeyDialog}>
                  <DialogTrigger asChild>
                    <Button>
                      <Plus className="mr-2 h-4 w-4" />
                      创建API密钥
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>创建新的API密钥</DialogTitle>
                      <DialogDescription>
                        为应用程序或服务创建新的API访问密钥
                      </DialogDescription>
                    </DialogHeader>
                    <div className="py-4">
                      <Label htmlFor="keyName">密钥名称</Label>
                      <Input id="keyName" placeholder="输入API密钥名称" />
                    </div>
                    <DialogFooter>
                      <Button variant="outline" onClick={() => setShowApiKeyDialog(false)}>
                        取消
                      </Button>
                      <Button onClick={() => createApiKey('新API密钥')}>
                        创建密钥
                      </Button>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>
              </CardTitle>
              <CardDescription>
                管理API访问密钥和权限配置
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {apiKeys.map((apiKey) => (
                  <div key={apiKey.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex-1">
                      <h4 className="font-medium">{apiKey.name}</h4>
                      <p className="text-sm text-gray-500 font-mono">{apiKey.key}</p>
                      <div className="flex items-center space-x-4 mt-2 text-xs text-gray-400">
                        <span>创建时间: {apiKey.createdAt}</span>
                        <span>最后使用: {apiKey.lastUsed}</span>
                      </div>
                    </div>
                    <div className="flex space-x-2">
                      <Button variant="outline" size="sm">
                        <Copy className="h-4 w-4" />
                      </Button>
                      <Button variant="outline" size="sm">
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => deleteApiKey(apiKey.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>

              <Alert className="mt-6">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  请妥善保管API密钥，避免泄露给未授权的第三方。如密钥泄露，请立即删除并重新生成。
                </AlertDescription>
              </Alert>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* 危险区域 */}
      <Card className="mt-6 border-red-200">
        <CardHeader>
          <CardTitle className="text-red-600">危险区域</CardTitle>
          <CardDescription>
            以下操作可能对系统造成不可逆的影响，请谨慎操作
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 border border-red-200 rounded-lg">
              <div>
                <h4 className="font-medium">重置系统设置</h4>
                <p className="text-sm text-gray-500">将所有设置恢复为默认值</p>
              </div>
              <Button variant="outline" onClick={handleResetSettings}>
                重置设置
              </Button>
            </div>
            <div className="flex items-center justify-between p-4 border border-red-200 rounded-lg">
              <div>
                <h4 className="font-medium">清空系统缓存</h4>
                <p className="text-sm text-gray-500">清除所有系统缓存数据</p>
              </div>
              <Button variant="outline">
                清空缓存
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}