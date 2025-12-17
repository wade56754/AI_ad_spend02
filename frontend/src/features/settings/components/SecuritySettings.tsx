/**
 * SecuritySettings Component
 *
 * Password change form and session management
 * Integrates with useAuth hook for password change
 *
 * SoT Reference: AUTH_SPEC.md v2.0
 */

'use client';

import React, { useState, useCallback } from 'react';
import {
  Lock,
  Shield,
  Smartphone,
  LogOut,
  Eye,
  EyeOff,
  AlertCircle,
  CheckCircle2,
  Loader2,
  Monitor,
  Clock,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { useAuth } from '@/features/auth';

// ============================================================
// Types
// ============================================================

interface PasswordFormState {
  current_password: string;
  new_password: string;
  confirm_password: string;
}

interface PasswordVisibility {
  current: boolean;
  new: boolean;
  confirm: boolean;
}

interface SessionInfo {
  id: string;
  device: string;
  location: string;
  last_active: string;
  is_current: boolean;
}

// ============================================================
// Mock Data
// ============================================================

const MOCK_SESSIONS: SessionInfo[] = [
  {
    id: '1',
    device: 'Chrome on Windows',
    location: '上海',
    last_active: '当前会话',
    is_current: true,
  },
  {
    id: '2',
    device: 'Safari on macOS',
    location: '北京',
    last_active: '2小时前',
    is_current: false,
  },
  {
    id: '3',
    device: 'Mobile App (iOS)',
    location: '深圳',
    last_active: '1天前',
    is_current: false,
  },
];

// ============================================================
// Password Validation
// ============================================================

function validatePassword(password: string): { valid: boolean; message: string } {
  if (password.length < 8) {
    return { valid: false, message: '密码长度至少8位' };
  }
  if (!/[A-Z]/.test(password)) {
    return { valid: false, message: '需要包含大写字母' };
  }
  if (!/[a-z]/.test(password)) {
    return { valid: false, message: '需要包含小写字母' };
  }
  if (!/[0-9]/.test(password)) {
    return { valid: false, message: '需要包含数字' };
  }
  return { valid: true, message: '密码强度良好' };
}

// ============================================================
// Component
// ============================================================

export function SecuritySettings() {
  const { changePassword, logout } = useAuth();

  // Password form state
  const [passwordForm, setPasswordForm] = useState<PasswordFormState>({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });

  // Password visibility toggles
  const [showPassword, setShowPassword] = useState<PasswordVisibility>({
    current: false,
    new: false,
    confirm: false,
  });

  // Form status
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [passwordSuccess, setPasswordSuccess] = useState(false);

  // Sessions state
  const [sessions] = useState<SessionInfo[]>(MOCK_SESSIONS);
  const [isLoggingOutAll, setIsLoggingOutAll] = useState(false);

  // Password validation result
  const passwordValidation = validatePassword(passwordForm.new_password);
  const passwordsMatch = passwordForm.new_password === passwordForm.confirm_password;

  // Handle password input change
  const handlePasswordChange = (field: keyof PasswordFormState, value: string) => {
    setPasswordForm(prev => ({ ...prev, [field]: value }));
    setPasswordError(null);
    setPasswordSuccess(false);
  };

  // Toggle password visibility
  const togglePasswordVisibility = (field: keyof PasswordVisibility) => {
    setShowPassword(prev => ({ ...prev, [field]: !prev[field] }));
  };

  // Handle password change submission
  const handleChangePassword = useCallback(async () => {
    // Validation
    if (!passwordForm.current_password) {
      setPasswordError('请输入当前密码');
      return;
    }
    if (!passwordValidation.valid) {
      setPasswordError(passwordValidation.message);
      return;
    }
    if (!passwordsMatch) {
      setPasswordError('两次输入的密码不一致');
      return;
    }

    setIsChangingPassword(true);
    setPasswordError(null);

    try {
      await changePassword({
        old_password: passwordForm.current_password,
        new_password: passwordForm.new_password,
      });
      
      setPasswordSuccess(true);
      setPasswordForm({
        current_password: '',
        new_password: '',
        confirm_password: '',
      });
    } catch (error) {
      setPasswordError('密码修改失败，请检查当前密码是否正确');
    } finally {
      setIsChangingPassword(false);
    }
  }, [passwordForm, passwordValidation, passwordsMatch, changePassword]);

  // Handle logout from all devices
  const handleLogoutAll = useCallback(async () => {
    setIsLoggingOutAll(true);
    try {
      // TODO: Implement logout all API
      await new Promise(resolve => setTimeout(resolve, 1000));
      await logout();
    } catch (error) {
      console.error('Failed to logout all sessions:', error);
    } finally {
      setIsLoggingOutAll(false);
    }
  }, [logout]);

  // Handle single session logout
  const handleLogoutSession = useCallback(async (sessionId: string) => {
    // TODO: Implement single session logout API
    console.log('Logout session:', sessionId);
  }, []);

  return (
    <div className="space-y-8">
      {/* Password Change Section */}
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <Lock className="h-4 w-4 text-primary" />
          <h3 className="text-sm font-semibold">修改密码</h3>
        </div>

        <div className="grid gap-4 max-w-md">
          {/* Current Password */}
          <div className="grid gap-2">
            <Label htmlFor="current_password">当前密码</Label>
            <div className="relative">
              <Input
                id="current_password"
                type={showPassword.current ? 'text' : 'password'}
                value={passwordForm.current_password}
                onChange={(e) => handlePasswordChange('current_password', e.target.value)}
                placeholder="输入当前密码"
                className="pr-10"
              />
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="absolute right-0 top-0 h-full px-3"
                onClick={() => togglePasswordVisibility('current')}
              >
                {showPassword.current ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </Button>
            </div>
          </div>

          {/* New Password */}
          <div className="grid gap-2">
            <Label htmlFor="new_password">新密码</Label>
            <div className="relative">
              <Input
                id="new_password"
                type={showPassword.new ? 'text' : 'password'}
                value={passwordForm.new_password}
                onChange={(e) => handlePasswordChange('new_password', e.target.value)}
                placeholder="输入新密码"
                className="pr-10"
              />
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="absolute right-0 top-0 h-full px-3"
                onClick={() => togglePasswordVisibility('new')}
              >
                {showPassword.new ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </Button>
            </div>
            {passwordForm.new_password && (
              <p className={`text-xs flex items-center gap-1 ${
                passwordValidation.valid ? 'text-green-600' : 'text-amber-600'
              }`}>
                {passwordValidation.valid ? (
                  <CheckCircle2 className="h-3 w-3" />
                ) : (
                  <AlertCircle className="h-3 w-3" />
                )}
                {passwordValidation.message}
              </p>
            )}
          </div>

          {/* Confirm Password */}
          <div className="grid gap-2">
            <Label htmlFor="confirm_password">确认新密码</Label>
            <div className="relative">
              <Input
                id="confirm_password"
                type={showPassword.confirm ? 'text' : 'password'}
                value={passwordForm.confirm_password}
                onChange={(e) => handlePasswordChange('confirm_password', e.target.value)}
                placeholder="再次输入新密码"
                className="pr-10"
              />
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="absolute right-0 top-0 h-full px-3"
                onClick={() => togglePasswordVisibility('confirm')}
              >
                {showPassword.confirm ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </Button>
            </div>
            {passwordForm.confirm_password && !passwordsMatch && (
              <p className="text-xs text-destructive flex items-center gap-1">
                <AlertCircle className="h-3 w-3" />
                两次输入的密码不一致
              </p>
            )}
          </div>

          {/* Error/Success Messages */}
          {passwordError && (
            <div className="p-3 bg-destructive/10 text-destructive rounded-md text-sm flex items-center gap-2">
              <AlertCircle className="h-4 w-4" />
              {passwordError}
            </div>
          )}
          {passwordSuccess && (
            <div className="p-3 bg-green-50 text-green-700 rounded-md text-sm flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4" />
              密码修改成功
            </div>
          )}

          {/* Submit Button */}
          <Button
            onClick={handleChangePassword}
            disabled={isChangingPassword || !passwordValidation.valid || !passwordsMatch}
            className="w-fit"
          >
            {isChangingPassword ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                修改中...
              </>
            ) : (
              <>
                <Lock className="mr-2 h-4 w-4" />
                修改密码
              </>
            )}
          </Button>
        </div>
      </div>

      <Separator />

      {/* Two-Factor Authentication Section */}
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <Shield className="h-4 w-4 text-primary" />
          <h3 className="text-sm font-semibold">两步验证</h3>
        </div>

        <div className="p-4 border rounded-lg flex items-center justify-between max-w-md">
          <div className="space-y-1">
            <p className="text-sm font-medium">双因素认证</p>
            <p className="text-xs text-muted-foreground">
              启用两步验证以增强账户安全性
            </p>
          </div>
          <Button variant="outline" size="sm">
            <Smartphone className="mr-2 h-4 w-4" />
            设置
          </Button>
        </div>
      </div>

      <Separator />

      {/* Active Sessions Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Monitor className="h-4 w-4 text-primary" />
            <h3 className="text-sm font-semibold">登录设备</h3>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={handleLogoutAll}
            disabled={isLoggingOutAll}
          >
            {isLoggingOutAll ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <LogOut className="mr-2 h-4 w-4" />
            )}
            登出所有设备
          </Button>
        </div>

        <div className="border rounded-lg divide-y">
          {sessions.map((session) => (
            <div
              key={session.id}
              className="p-4 flex items-center justify-between"
            >
              <div className="flex items-start gap-3">
                <Monitor className="h-5 w-5 text-muted-foreground mt-0.5" />
                <div className="space-y-1">
                  <p className="text-sm font-medium flex items-center gap-2">
                    {session.device}
                    {session.is_current && (
                      <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded">
                        当前
                      </span>
                    )}
                  </p>
                  <p className="text-xs text-muted-foreground flex items-center gap-2">
                    <span>{session.location}</span>
                    <span className="text-muted-foreground/50">|</span>
                    <Clock className="h-3 w-3" />
                    <span>{session.last_active}</span>
                  </p>
                </div>
              </div>
              {!session.is_current && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleLogoutSession(session.id)}
                >
                  <LogOut className="h-4 w-4" />
                </Button>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default SecuritySettings;
