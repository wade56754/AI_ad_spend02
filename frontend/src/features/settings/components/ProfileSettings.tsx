/**
 * ProfileSettings Component
 *
 * Displays and allows editing of user profile information
 * Including username, email, full name, and avatar
 *
 * SoT Reference: AUTH_SPEC.md v2.0
 */

'use client';

import React, { useState } from 'react';
import { User, Mail, UserCircle, Camera, Badge } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar';
import { Separator } from '@/components/ui/separator';
import type { User as UserType } from '@/features/auth/types';
import { USER_ROLE_CONFIG, UserRole } from '@/features/auth/types';

// ============================================================
// Types
// ============================================================

interface ProfileSettingsProps {
  user: UserType | null;
  onChange?: () => void;
}

interface ProfileFormState {
  username: string;
  email: string;
  full_name: string;
}

// ============================================================
// Helper Functions
// ============================================================

function getInitials(name?: string, username?: string): string {
  if (name) {
    const parts = name.split(' ');
    return parts.map(p => p.charAt(0)).join('').toUpperCase().slice(0, 2);
  }
  if (username) {
    return username.charAt(0).toUpperCase();
  }
  return 'U';
}

function getRoleLabel(role?: UserRole): string {
  if (!role) return '未知角色';
  return USER_ROLE_CONFIG[role]?.label || role;
}

// ============================================================
// Component
// ============================================================

export function ProfileSettings({ user, onChange }: ProfileSettingsProps) {
  // Form state - 直接从 props 初始化，避免不必要的 useEffect 同步
  // 当 user prop 变化时，组件会重新渲染并使用新的初始值
  const [profile, setProfile] = useState<ProfileFormState>(() => ({
    username: user?.username || '',
    email: user?.email || '',
    full_name: user?.full_name || '',
  }));

  // Handle input changes
  const handleInputChange = (field: keyof ProfileFormState, value: string) => {
    setProfile(prev => ({ ...prev, [field]: value }));
    onChange?.();
  };

  // Handle avatar upload (placeholder)
  const handleAvatarUpload = () => {
    // TODO: Implement file upload
    console.log('Avatar upload clicked');
  };

  return (
    <div className="space-y-6">
      {/* Avatar Section */}
      <div className="flex items-center gap-6">
        <div className="relative">
          <Avatar className="h-20 w-20">
            <AvatarImage src={undefined} alt={profile.full_name || profile.username} />
            <AvatarFallback className="text-lg bg-primary/10 text-primary">
              {getInitials(profile.full_name, profile.username)}
            </AvatarFallback>
          </Avatar>
          <Button
            variant="outline"
            size="icon"
            className="absolute -bottom-1 -right-1 h-8 w-8 rounded-full"
            onClick={handleAvatarUpload}
          >
            <Camera className="h-4 w-4" />
          </Button>
        </div>
        <div>
          <h3 className="text-lg font-medium">
            {profile.full_name || profile.username || '用户'}
          </h3>
          <p className="text-sm text-muted-foreground flex items-center gap-1">
            <Badge className="h-3 w-3" />
            {getRoleLabel(user?.role)}
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            点击头像更换照片（可选）
          </p>
        </div>
      </div>

      <Separator />

      {/* Form Fields */}
      <div className="grid gap-6">
        {/* Username */}
        <div className="grid gap-2">
          <Label htmlFor="username" className="flex items-center gap-2">
            <User className="h-4 w-4" />
            用户名
          </Label>
          <Input
            id="username"
            type="text"
            value={profile.username}
            onChange={(e) => handleInputChange('username', e.target.value)}
            placeholder="输入用户名"
            className="max-w-md"
          />
          <p className="text-xs text-muted-foreground">
            用户名用于系统登录，修改后需要使用新用户名登录
          </p>
        </div>

        {/* Email */}
        <div className="grid gap-2">
          <Label htmlFor="email" className="flex items-center gap-2">
            <Mail className="h-4 w-4" />
            邮箱地址
          </Label>
          <Input
            id="email"
            type="email"
            value={profile.email}
            onChange={(e) => handleInputChange('email', e.target.value)}
            placeholder="输入邮箱地址"
            className="max-w-md"
          />
          <p className="text-xs text-muted-foreground">
            用于接收系统通知和找回密码
          </p>
        </div>

        {/* Full Name */}
        <div className="grid gap-2">
          <Label htmlFor="full_name" className="flex items-center gap-2">
            <UserCircle className="h-4 w-4" />
            真实姓名
          </Label>
          <Input
            id="full_name"
            type="text"
            value={profile.full_name}
            onChange={(e) => handleInputChange('full_name', e.target.value)}
            placeholder="输入真实姓名"
            className="max-w-md"
          />
          <p className="text-xs text-muted-foreground">
            将显示在系统界面和报表中
          </p>
        </div>
      </div>

      {/* Account Info (Read-only) */}
      <Separator />

      <div className="space-y-4">
        <h4 className="text-sm font-medium text-muted-foreground">账户信息</h4>
        <div className="grid gap-4 text-sm">
          <div className="flex justify-between items-center py-2 px-3 bg-muted/50 rounded-md max-w-md">
            <span className="text-muted-foreground">账户ID</span>
            <span className="font-mono">{user?.id || '-'}</span>
          </div>
          <div className="flex justify-between items-center py-2 px-3 bg-muted/50 rounded-md max-w-md">
            <span className="text-muted-foreground">角色</span>
            <span>{getRoleLabel(user?.role)}</span>
          </div>
          <div className="flex justify-between items-center py-2 px-3 bg-muted/50 rounded-md max-w-md">
            <span className="text-muted-foreground">创建时间</span>
            <span>
              {user?.created_at
                ? new Date(user.created_at).toLocaleDateString('zh-CN')
                : '-'}
            </span>
          </div>
          <div className="flex justify-between items-center py-2 px-3 bg-muted/50 rounded-md max-w-md">
            <span className="text-muted-foreground">最近登录</span>
            <span>
              {user?.last_login
                ? new Date(user.last_login).toLocaleString('zh-CN')
                : '-'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ProfileSettings;
