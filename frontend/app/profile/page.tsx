'use client';

import { useState, useEffect } from 'react';
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
  Avatar,
  AvatarFallback,
  AvatarImage,
} from '@/components/ui/avatar';
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
  User,
  Mail,
  Phone,
  Building,
  Calendar,
  Shield,
  Bell,
  Smartphone,
  Key,
  Camera,
  Save,
  Eye,
  EyeOff,
  Copy,
  RefreshCw,
  Download,
  Upload,
  CheckCircle,
  AlertTriangle,
  Settings,
  Clock,
  TrendingUp,
  BarChart3,
  DollarSign,
  Users,
  Target,
  Activity,
} from 'lucide-react';
import { toast } from 'sonner';

interface UserProfile {
  id: string;
  email: string;
  fullName: string;
  phone: string;
  company: string;
  role: string;
  avatar: string;
  timezone: string;
  language: string;
  dateFormat: string;
  currency: string;
  emailNotifications: boolean;
  pushNotifications: boolean;
  smsNotifications: boolean;
  createdAt: string;
  lastLogin: string;
  twoFactorEnabled: boolean;
  apiKeys: Array<{
    id: string;
    name: string;
    key: string;
    createdAt: string;
    lastUsed: string;
  }>;
}

export default function ProfilePage() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState('profile');
  const [showPasswordDialog, setShowPasswordDialog] = useState(false);
  const [showAvatarDialog, setShowAvatarDialog] = useState(false);
  const [showApiKeyDialog, setShowApiKeyDialog] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPasswords, setShowPasswords] = useState({
    current: false,
    new: false,
    confirm: false,
  });

  const [profile, setProfile] = useState<UserProfile>({
    id: '1',
    email: 'manager@example.com',
    fullName: '张经理',
    phone: '13800138002',
    company: '广告代理公司',
    role: 'manager',
    avatar: '',
    timezone: 'Asia/Shanghai',
    language: 'zh-CN',
    dateFormat: 'YYYY-MM-DD',
    currency: 'CNY',
    emailNotifications: true,
    pushNotifications: true,
    smsNotifications: false,
    createdAt: '2024-01-01T00:00:00Z',
    lastLogin: '2024-01-15T10:30:00Z',
    twoFactorEnabled: false,
    apiKeys: [
      {
        id: '1',
        name: '个人API密钥',
        key: 'sk_pers_1234567890abcdef',
        createdAt: '2024-01-10',
        lastUsed: '2024-01-15',
      },
    ],
  });

  const [statistics] = useState({
    projectsCount: 5,
    adAccountsCount: 12,
    totalSpend: 1250000,
    totalConversions: 8950,
    avgCTR: 2.3,
    avgCPC: 3.2,
  });

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    setLoading(true);
    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 1000));
      // profile数据已通过useState初始化
    } catch (error) {
      console.error('获取用户资料失败:', error);
      toast.error('获取用户资料失败');
    } finally {
      setLoading(false);
    }
  };

  const saveProfile = async () => {
    setSaving(true);
    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 1000));
      toast.success('个人资料保存成功');
    } catch (error) {
      console.error('保存个人资料失败:', error);
      toast.error('保存个人资料失败');
    } finally {
      setSaving(false);
    }
  };

  const updateProfile = (key: keyof UserProfile, value: any) => {
    setProfile(prev => ({
      ...prev,
      [key]: value,
    }));
  };

  const changePassword = async () => {
    if (newPassword !== confirmPassword) {
      toast.error('新密码与确认密码不匹配');
      return;
    }

    if (newPassword.length < 8) {
      toast.error('密码长度至少8位');
      return;
    }

    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 1000));

      toast.success('密码修改成功');
      setShowPasswordDialog(false);
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (error) {
      console.error('修改密码失败:', error);
      toast.error('修改密码失败');
    }
  };

  const enableTwoFactor = async () => {
    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 1000));

      updateProfile('twoFactorEnabled', true);
      toast.success('双因素认证已启用');
    } catch (error) {
      console.error('启用双因素认证失败:', error);
      toast.error('启用双因素认证失败');
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

      setProfile(prev => ({
        ...prev,
        apiKeys: [newKey, ...prev.apiKeys],
      }));

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

      setProfile(prev => ({
        ...prev,
        apiKeys: prev.apiKeys.filter(k => k.id !== keyId),
      }));

      toast.success('API密钥删除成功');
    } catch (error) {
      console.error('删除API密钥失败:', error);
      toast.error('删除API密钥失败');
    }
  };

  const copyApiKey = (key: string) => {
    navigator.clipboard.writeText(key);
    toast.success('API密钥已复制到剪贴板');
  };

  const getRoleText = (role: string) => {
    const roleMap = {
      admin: '管理员',
      manager: '项目经理',
      advertiser: '广告主',
      publisher: '发布商',
      finance: '财务',
    };
    return roleMap[role as keyof typeof roleMap] || role;
  };

  const getRoleBadgeVariant = (role: string) => {
    switch (role) {
      case 'admin': return 'destructive';
      case 'manager': return 'default';
      case 'advertiser': return 'secondary';
      case 'publisher': return 'outline';
      case 'finance': return 'purple';
      default: return 'outline';
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">个人中心</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            管理个人资料、安全设置和通知偏好
          </p>
        </div>
        <Button onClick={saveProfile} disabled={saving}>
          {saving ? (
            <>
              <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
              保存中...
            </>
          ) : (
            <>
              <Save className="mr-2 h-4 w-4" />
              保存更改
            </>
          )}
        </Button>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="profile">个人资料</TabsTrigger>
          <TabsTrigger value="statistics">数据统计</TabsTrigger>
          <TabsTrigger value="security">安全设置</TabsTrigger>
          <TabsTrigger value="notifications">通知设置</TabsTrigger>
          <TabsTrigger value="api">API管理</TabsTrigger>
        </TabsList>

        {/* 个人资料 */}
        <TabsContent value="profile">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="lg:col-span-1">
              <CardHeader>
                <CardTitle>头像</CardTitle>
                <CardDescription>更新您的个人头像</CardDescription>
              </CardHeader>
              <CardContent className="flex flex-col items-center space-y-4">
                <Avatar className="h-24 w-24">
                  <AvatarImage src={profile.avatar} />
                  <AvatarFallback className="text-2xl">
                    {profile.fullName.charAt(0)}
                  </AvatarFallback>
                </Avatar>
                <Dialog open={showAvatarDialog} onOpenChange={setShowAvatarDialog}>
                  <DialogTrigger asChild>
                    <Button variant="outline">
                      <Camera className="mr-2 h-4 w-4" />
                      更换头像
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>更换头像</DialogTitle>
                      <DialogDescription>
                        选择新的头像图片
                      </DialogDescription>
                    </DialogHeader>
                    <div className="py-4">
                      <Input type="file" accept="image/*" />
                    </div>
                    <DialogFooter>
                      <Button variant="outline" onClick={() => setShowAvatarDialog(false)}>
                        取消
                      </Button>
                      <Button>上传头像</Button>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>
                <div className="text-center">
                  <Badge variant={getRoleBadgeVariant(profile.role)}>
                    {getRoleText(profile.role)}
                  </Badge>
                </div>
              </CardContent>
            </Card>

            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>基本信息</CardTitle>
                <CardDescription>更新您的个人信息</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <Label htmlFor="fullName">姓名</Label>
                    <Input
                      id="fullName"
                      value={profile.fullName}
                      onChange={(e) => updateProfile('fullName', e.target.value)}
                    />
                  </div>
                  <div>
                    <Label htmlFor="email">邮箱</Label>
                    <Input
                      id="email"
                      type="email"
                      value={profile.email}
                      disabled
                      className="bg-gray-50"
                    />
                  </div>
                  <div>
                    <Label htmlFor="phone">电话</Label>
                    <Input
                      id="phone"
                      value={profile.phone}
                      onChange={(e) => updateProfile('phone', e.target.value)}
                    />
                  </div>
                  <div>
                    <Label htmlFor="company">公司</Label>
                    <Input
                      id="company"
                      value={profile.company}
                      onChange={(e) => updateProfile('company', e.target.value)}
                    />
                  </div>
                </div>

                <div className="border-t pt-6">
                  <h4 className="text-lg font-medium mb-4">偏好设置</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <Label htmlFor="timezone">时区</Label>
                      <Select
                        value={profile.timezone}
                        onValueChange={(value) => updateProfile('timezone', value)}
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
                        value={profile.language}
                        onValueChange={(value) => updateProfile('language', value)}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="zh-CN">简体中文</SelectItem>
                          <SelectItem value="zh-TW">繁体中文</SelectItem>
                          <SelectItem value="en-US">English</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* 数据统计 */}
        <TabsContent value="statistics">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <Target className="h-6 w-6 text-blue-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                      项目数量
                    </p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {statistics.projectsCount}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center">
                  <div className="p-2 bg-green-100 rounded-lg">
                    <Users className="h-6 w-6 text-green-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                      广告账户
                    </p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {statistics.adAccountsCount}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center">
                  <div className="p-2 bg-yellow-100 rounded-lg">
                    <DollarSign className="h-6 w-6 text-yellow-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                      总消费
                    </p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      ¥{statistics.totalSpend.toLocaleString()}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center">
                  <div className="p-2 bg-purple-100 rounded-lg">
                    <Activity className="h-6 w-6 text-purple-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                      总转化数
                    </p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {statistics.totalConversions.toLocaleString()}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center">
                  <div className="p-2 bg-red-100 rounded-lg">
                    <BarChart3 className="h-6 w-6 text-red-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                      平均CTR
                    </p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {statistics.avgCTR}%
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center">
                  <div className="p-2 bg-indigo-100 rounded-lg">
                    <TrendingUp className="h-6 w-6 text-indigo-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                      平均CPC
                    </p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      ¥{statistics.avgCPC}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card className="mt-6">
            <CardHeader>
              <CardTitle>账户活动</CardTitle>
              <CardDescription>
                查看您的账户使用情况
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex items-center space-x-3">
                    <Calendar className="h-5 w-5 text-gray-400" />
                    <div>
                      <p className="font-medium">注册时间</p>
                      <p className="text-sm text-gray-500">
                        {new Date(profile.createdAt).toLocaleString('zh-CN')}
                      </p>
                    </div>
                  </div>
                </div>
                <div className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex items-center space-x-3">
                    <Clock className="h-5 w-5 text-gray-400" />
                    <div>
                      <p className="font-medium">最后登录</p>
                      <p className="text-sm text-gray-500">
                        {new Date(profile.lastLogin).toLocaleString('zh-CN')}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 安全设置 */}
        <TabsContent value="security">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>密码安全</CardTitle>
                <CardDescription>管理您的密码和访问权限</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Dialog open={showPasswordDialog} onOpenChange={setShowPasswordDialog}>
                  <DialogTrigger asChild>
                    <Button variant="outline">
                      <Key className="mr-2 h-4 w-4" />
                      修改密码
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>修改密码</DialogTitle>
                      <DialogDescription>
                        为了您的账户安全，请设置强密码
                      </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4">
                      <div>
                        <Label htmlFor="currentPassword">当前密码</Label>
                        <div className="relative">
                          <Input
                            id="currentPassword"
                            type={showPasswords.current ? 'text' : 'password'}
                            value={currentPassword}
                            onChange={(e) => setCurrentPassword(e.target.value)}
                          />
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            className="absolute right-0 top-0 h-full px-3"
                            onClick={() => setShowPasswords(prev => ({
                              ...prev,
                              current: !prev.current
                            }))}
                          >
                            {showPasswords.current ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                          </Button>
                        </div>
                      </div>
                      <div>
                        <Label htmlFor="newPassword">新密码</Label>
                        <div className="relative">
                          <Input
                            id="newPassword"
                            type={showPasswords.new ? 'text' : 'password'}
                            value={newPassword}
                            onChange={(e) => setNewPassword(e.target.value)}
                          />
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            className="absolute right-0 top-0 h-full px-3"
                            onClick={() => setShowPasswords(prev => ({
                              ...prev,
                              new: !prev.new
                            }))}
                          >
                            {showPasswords.new ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                          </Button>
                        </div>
                      </div>
                      <div>
                        <Label htmlFor="confirmPassword">确认新密码</Label>
                        <div className="relative">
                          <Input
                            id="confirmPassword"
                            type={showPasswords.confirm ? 'text' : 'password'}
                            value={confirmPassword}
                            onChange={(e) => setConfirmPassword(e.target.value)}
                          />
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            className="absolute right-0 top-0 h-full px-3"
                            onClick={() => setShowPasswords(prev => ({
                              ...prev,
                              confirm: !prev.confirm
                            }))}
                          >
                            {showPasswords.confirm ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                          </Button>
                        </div>
                      </div>
                    </div>
                    <DialogFooter>
                      <Button variant="outline" onClick={() => setShowPasswordDialog(false)}>
                        取消
                      </Button>
                      <Button onClick={changePassword}>
                        修改密码
                      </Button>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>双因素认证</CardTitle>
                <CardDescription>增强您的账户安全性</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex items-center space-x-3">
                    <Smartphone className="h-5 w-5 text-gray-400" />
                    <div>
                      <p className="font-medium">双因素认证</p>
                      <p className="text-sm text-gray-500">
                        {profile.twoFactorEnabled ? '已启用' : '未启用'}
                      </p>
                    </div>
                  </div>
                  {profile.twoFactorEnabled ? (
                    <Badge variant="default">
                      <CheckCircle className="w-3 h-3 mr-1" />
                      已启用
                    </Badge>
                  ) : (
                    <Button onClick={enableTwoFactor}>
                      <Shield className="mr-2 h-4 w-4" />
                      启用
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
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
                配置您的通知偏好和接收方式
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div className="space-y-0.5">
                  <Label>邮件通知</Label>
                  <p className="text-sm text-gray-500">通过邮件接收系统通知</p>
                </div>
                <Switch
                  checked={profile.emailNotifications}
                  onCheckedChange={(checked) => updateProfile('emailNotifications', checked)}
                />
              </div>
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div className="space-y-0.5">
                  <Label>推送通知</Label>
                  <p className="text-sm text-gray-500">通过浏览器推送接收通知</p>
                </div>
                <Switch
                  checked={profile.pushNotifications}
                  onCheckedChange={(checked) => updateProfile('pushNotifications', checked)}
                />
              </div>
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div className="space-y-0.5">
                  <Label>短信通知</Label>
                  <p className="text-sm text-gray-500">通过短信接收紧急通知</p>
                </div>
                <Switch
                  checked={profile.smsNotifications}
                  onCheckedChange={(checked) => updateProfile('smsNotifications', checked)}
                />
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
                  <Key className="mr-2 h-5 w-5" />
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
                        为您的应用程序创建新的API访问密钥
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
                管理您的API访问密钥
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {profile.apiKeys.map((apiKey) => (
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
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => copyApiKey(apiKey.key)}
                      >
                        <Copy className="h-4 w-4" />
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
                  请妥善保管您的API密钥，避免泄露给未授权的第三方。
                </AlertDescription>
              </Alert>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}