'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import {
  Eye,
  EyeOff,
  UserPlus,
  Mail,
  Lock,
  User,
  Building,
  AlertCircle,
  CheckCircle,
  ArrowRight,
  Shield,
  Zap,
  Users,
  Check,
  X,
  Loader2,
} from 'lucide-react';
import { toast } from 'sonner';

export default function SignUpPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    fullName: '',
    company: '',
    phone: '',
    role: 'advertiser', // advertiser, agency, individual
    agreeTerms: false,
    subscribeNewsletter: false,
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [passwordStrength, setPasswordStrength] = useState(0);
  const [availableEmail, setAvailableEmail] = useState<boolean | null>(null);

  const redirectUrl = searchParams.get('redirect') || '/';

  // 检查是否已经登录
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      router.push(redirectUrl);
    }
  }, [router, redirectUrl]);

  // 密码强度检查
  useEffect(() => {
    if (!formData.password) {
      setPasswordStrength(0);
      return;
    }

    let strength = 0;
    if (formData.password.length >= 8) strength++;
    if (formData.password.length >= 12) strength++;
    if (/[a-z]/.test(formData.password) && /[A-Z]/.test(formData.password)) strength++;
    if (/\d/.test(formData.password)) strength++;
    if (/[!@#$%^&*(),.?":{}|<>]/.test(formData.password)) strength++;

    setPasswordStrength(strength);
  }, [formData.password]);

  // 邮箱可用性检查
  useEffect(() => {
    if (formData.email && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      const checkEmailTimer = setTimeout(() => {
        checkEmailAvailability();
      }, 500);

      return () => clearTimeout(checkEmailTimer);
    } else {
      setAvailableEmail(null);
    }
  }, [formData.email]);

  const checkEmailAvailability = async () => {
    try {
      const response = await fetch(`/api/v1/auth/check-email?email=${formData.email}`);
      const result = await response.json();
      setAvailableEmail(result.available);
    } catch (error) {
      console.error('检查邮箱可用性失败:', error);
      setAvailableEmail(null);
    }
  };

  const validateStep1 = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.email.trim()) {
      newErrors.email = '请输入邮箱地址';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = '请输入有效的邮箱地址';
    } else if (availableEmail === false) {
      newErrors.email = '该邮箱地址已被注册';
    }

    if (!formData.password.trim()) {
      newErrors.password = '请输入密码';
    } else if (formData.password.length < 8) {
      newErrors.password = '密码长度至少8位';
    } else if (passwordStrength < 3) {
      newErrors.password = '密码强度太弱，请包含大小写字母、数字和特殊字符';
    }

    if (!formData.confirmPassword.trim()) {
      newErrors.confirmPassword = '请确认密码';
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = '两次输入的密码不一致';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const validateStep2 = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.fullName.trim()) {
      newErrors.fullName = '请输入姓名';
    } else if (formData.fullName.length < 2) {
      newErrors.fullName = '姓名至少2个字符';
    }

    if (!formData.company.trim()) {
      newErrors.company = '请输入公司名称';
    }

    if (!formData.phone.trim()) {
      newErrors.phone = '请输入手机号码';
    } else if (!/^1[3-9]\d{9}$/.test(formData.phone)) {
      newErrors.phone = '请输入有效的手机号码';
    }

    if (!formData.agreeTerms) {
      newErrors.agreeTerms = '请同意服务条款和隐私政策';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNextStep = () => {
    if (step === 1 && validateStep1()) {
      setStep(2);
      setErrors({});
    }
  };

  const handlePrevStep = () => {
    setStep(1);
    setErrors({});
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (step === 1) {
      handleNextStep();
      return;
    }

    if (!validateStep2()) {
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('/api/v1/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      const result = await response.json();

      if (result.success) {
        toast.success('注册成功！请查收邮件验证账户');
        router.push(`/auth/sign-up-success?email=${formData.email}`);
      } else {
        setErrors({ submit: result.message || '注册失败，请检查信息后重试' });
      }
    } catch (error) {
      console.error('注册错误:', error);
      setErrors({ submit: '注册失败，请检查网络连接' });
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));

    // 清除对应字段的错误
    if (errors[name]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  const getPasswordStrengthText = () => {
    if (passwordStrength === 0) return '';
    if (passwordStrength <= 2) return '弱';
    if (passwordStrength <= 3) return '中';
    return '强';
  };

  const getPasswordStrengthColor = () => {
    if (passwordStrength <= 2) return 'bg-red-500';
    if (passwordStrength <= 3) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-6">
        {/* 头部Logo和标题 */}
        <div className="text-center">
          <div className="mx-auto h-12 w-12 bg-blue-600 rounded-full flex items-center justify-center mb-4">
            <Shield className="h-6 w-6 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            AI广告代投系统
          </h1>
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
            智能化广告投放管理平台
          </p>
        </div>

        {/* 注册进度 */}
        <div className="flex items-center justify-center space-x-4">
          <div className={`flex items-center ${step >= 1 ? 'text-blue-600' : 'text-gray-400'}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
              step >= 1 ? 'bg-blue-600 text-white' : 'bg-gray-200'
            }`}>
              {step > 1 ? <Check className="w-4 h-4" /> : '1'}
            </div>
            <span className="ml-2 text-sm">账户信息</span>
          </div>
          <div className={`w-8 h-0.5 ${step >= 2 ? 'bg-blue-600' : 'bg-gray-200'}`}></div>
          <div className={`flex items-center ${step >= 2 ? 'text-blue-600' : 'text-gray-400'}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
              step >= 2 ? 'bg-blue-600 text-white' : 'bg-gray-200'
            }`}>
              {step > 2 ? <Check className="w-4 h-4" /> : '2'}
            </div>
            <span className="ml-2 text-sm">详细信息</span>
          </div>
        </div>

        {/* 注册卡片 */}
        <Card>
          <CardHeader className="text-center">
            <CardTitle className="text-xl">创建新账户</CardTitle>
            <CardDescription>
              {step === 1 ? '请设置您的账户信息' : '请完善您的详细信息'}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* 错误提示 */}
            {errors.submit && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{errors.submit}</AlertDescription>
              </Alert>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              {step === 1 ? (
                // 第一步：账户信息
                <>
                  <div>
                    <Label htmlFor="email">邮箱地址</Label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                      <Input
                        id="email"
                        name="email"
                        type="email"
                        placeholder="请输入邮箱地址"
                        value={formData.email}
                        onChange={handleInputChange}
                        className={`pl-10 pr-10 ${
                          availableEmail === false ? 'border-red-300' :
                          availableEmail === true ? 'border-green-300' : ''
                        }`}
                        disabled={loading}
                        aria-invalid={!!errors.email}
                      />
                      {formData.email && (
                        <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                          {availableEmail === false && <X className="h-4 w-4 text-red-500" />}
                          {availableEmail === true && <Check className="h-4 w-4 text-green-500" />}
                          {availableEmail === null && <Loader2 className="h-4 w-4 text-gray-400 animate-spin" />}
                        </div>
                      )}
                    </div>
                    {errors.email && (
                      <p className="text-sm text-red-600 mt-1">{errors.email}</p>
                    )}
                    {availableEmail === true && (
                      <p className="text-sm text-green-600 mt-1">该邮箱地址可用</p>
                    )}
                  </div>

                  <div>
                    <Label htmlFor="password">密码</Label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                      <Input
                        id="password"
                        name="password"
                        type={showPassword ? 'text' : 'password'}
                        placeholder="请输入密码"
                        value={formData.password}
                        onChange={handleInputChange}
                        className="pl-10 pr-10"
                        disabled={loading}
                        aria-invalid={!!errors.password}
                      />
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="absolute right-1 top-1/2 transform -translate-y-1/2 h-6 w-6 p-0"
                        onClick={() => setShowPassword(!showPassword)}
                        disabled={loading}
                      >
                        {showPassword ? (
                          <EyeOff className="h-4 w-4" />
                        ) : (
                          <Eye className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                    {errors.password && (
                      <p className="text-sm text-red-600 mt-1">{errors.password}</p>
                    )}
                    {/* 密码强度指示器 */}
                    {formData.password && (
                      <div className="mt-2">
                        <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
                          <span>密码强度</span>
                          <span className="font-medium">{getPasswordStrengthText()}</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-1.5">
                          <div
                            className={`h-1.5 rounded-full transition-all duration-300 ${getPasswordStrengthColor()}`}
                            style={{ width: `${(passwordStrength / 5) * 100}%` }}
                          ></div>
                        </div>
                      </div>
                    )}
                  </div>

                  <div>
                    <Label htmlFor="confirmPassword">确认密码</Label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                      <Input
                        id="confirmPassword"
                        name="confirmPassword"
                        type={showConfirmPassword ? 'text' : 'password'}
                        placeholder="请再次输入密码"
                        value={formData.confirmPassword}
                        onChange={handleInputChange}
                        className={`pl-10 pr-10 ${
                          formData.confirmPassword && formData.password !== formData.confirmPassword
                            ? 'border-red-300'
                            : formData.confirmPassword && formData.password === formData.confirmPassword
                            ? 'border-green-300'
                            : ''
                        }`}
                        disabled={loading}
                        aria-invalid={!!errors.confirmPassword}
                      />
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="absolute right-1 top-1/2 transform -translate-y-1/2 h-6 w-6 p-0"
                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                        disabled={loading}
                      >
                        {showConfirmPassword ? (
                          <EyeOff className="h-4 w-4" />
                        ) : (
                          <Eye className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                    {errors.confirmPassword && (
                      <p className="text-sm text-red-600 mt-1">{errors.confirmPassword}</p>
                    )}
                    {formData.confirmPassword && formData.password === formData.confirmPassword && (
                      <p className="text-sm text-green-600 mt-1">密码匹配</p>
                    )}
                  </div>
                </>
              ) : (
                // 第二步：详细信息
                <>
                  <div>
                    <Label htmlFor="fullName">姓名</Label>
                    <div className="relative">
                      <User className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                      <Input
                        id="fullName"
                        name="fullName"
                        type="text"
                        placeholder="请输入您的真实姓名"
                        value={formData.fullName}
                        onChange={handleInputChange}
                        className="pl-10"
                        disabled={loading}
                        aria-invalid={!!errors.fullName}
                      />
                    </div>
                    {errors.fullName && (
                      <p className="text-sm text-red-600 mt-1">{errors.fullName}</p>
                    )}
                  </div>

                  <div>
                    <Label htmlFor="company">公司名称</Label>
                    <div className="relative">
                      <Building className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                      <Input
                        id="company"
                        name="company"
                        type="text"
                        placeholder="请输入公司名称"
                        value={formData.company}
                        onChange={handleInputChange}
                        className="pl-10"
                        disabled={loading}
                        aria-invalid={!!errors.company}
                      />
                    </div>
                    {errors.company && (
                      <p className="text-sm text-red-600 mt-1">{errors.company}</p>
                    )}
                  </div>

                  <div>
                    <Label htmlFor="phone">手机号码</Label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                      <Input
                        id="phone"
                        name="phone"
                        type="tel"
                        placeholder="请输入手机号码"
                        value={formData.phone}
                        onChange={handleInputChange}
                        className="pl-10"
                        disabled={loading}
                        aria-invalid={!!errors.phone}
                      />
                    </div>
                    {errors.phone && (
                      <p className="text-sm text-red-600 mt-1">{errors.phone}</p>
                    )}
                  </div>

                  <div>
                    <Label htmlFor="role">用户类型</Label>
                    <div className="grid grid-cols-1 gap-3">
                      {[
                        { value: 'advertiser', label: '广告主', desc: '直接投放广告的企业或个人' },
                        { value: 'agency', label: '代理商', desc: '为多个客户管理广告投投放' },
                        { value: 'individual', label: '个人用户', desc: '个人广告投手或顾问' },
                      ].map((role) => (
                        <div
                          key={role.value}
                          className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                            formData.role === role.value
                              ? 'border-blue-500 bg-blue-50'
                              : 'border-gray-200 hover:border-gray-300'
                          }`}
                          onClick={() => setFormData(prev => ({ ...prev, role: role.value }))}
                        >
                          <div className="flex items-center">
                            <input
                              type="radio"
                              name="role"
                              value={role.value}
                              checked={formData.role === role.value}
                              onChange={handleInputChange}
                              className="mr-3"
                              disabled={loading}
                            />
                            <div>
                              <div className="font-medium text-sm">{role.label}</div>
                              <div className="text-xs text-gray-500">{role.desc}</div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="space-y-3">
                    <div className="flex items-start space-x-2">
                      <Checkbox
                        id="agreeTerms"
                        checked={formData.agreeTerms}
                        onCheckedChange={(checked) => setFormData(prev => ({ ...prev, agreeTerms: checked }))}
                        disabled={loading}
                      />
                      <Label htmlFor="agreeTerms" className="text-sm text-gray-600 dark:text-gray-400">
                        我已阅读并同意
                        <Link href="/terms" className="text-blue-600 hover:text-blue-500 mx-1">
                          服务条款
                        </Link>
                        和
                        <Link href="/privacy" className="text-blue-600 hover:text-blue-500 ml-1">
                          隐私政策
                        </Link>
                      </Label>
                    </div>
                    {errors.agreeTerms && (
                      <p className="text-sm text-red-600">{errors.agreeTerms}</p>
                    )}

                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="subscribeNewsletter"
                        checked={formData.subscribeNewsletter}
                        onCheckedChange={(checked) => setFormData(prev => ({ ...prev, subscribeNewsletter: checked }))}
                        disabled={loading}
                      />
                      <Label htmlFor="subscribeNewsletter" className="text-sm text-gray-600 dark:text-gray-400">
                        订阅产品更新和营销资讯
                      </Label>
                    </div>
                  </div>
                </>
              )}

              <div className="flex space-x-3">
                {step === 2 && (
                  <Button
                    type="button"
                    variant="outline"
                    onClick={handlePrevStep}
                    disabled={loading}
                    className="flex-1"
                  >
                    上一步
                  </Button>
                )}
                <Button
                  type="submit"
                  className="flex-1"
                  disabled={loading}
                >
                  {loading ? (
                    <div className="flex items-center justify-center">
                      <Loader2 className="animate-spin -ml-1 mr-2 h-4 w-4" />
                      {step === 1 ? '验证中...' : '注册中...'}
                    </div>
                  ) : (
                    <div className="flex items-center justify-center">
                      {step === 1 ? (
                        <>
                          下一步
                          <ArrowRight className="ml-2 h-4 w-4" />
                        </>
                      ) : (
                        <>
                          <UserPlus className="mr-2 h-4 w-4" />
                          注册账户
                        </>
                      )}
                    </div>
                  )}
                </Button>
              </div>
            </form>
          </CardContent>

          <div className="p-6 text-center border-t">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              已有账户？
              <Link
                href="/auth/login"
                className="ml-1 font-medium text-blue-600 hover:text-blue-500"
              >
                立即登录
              </Link>
            </p>
          </div>
        </Card>

        {/* 功能特性卡片 */}
        <div className="grid grid-cols-1 gap-4">
          <Card className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Zap className="h-5 w-5 text-blue-600" />
              </div>
              <div className="flex-1">
                <h3 className="font-medium text-sm">智能分析</h3>
                <p className="text-xs text-gray-600">AI驱动的账户性能分析和优化建议</p>
              </div>
            </div>
          </Card>

          <Card className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <Users className="h-5 w-5 text-green-600" />
              </div>
              <div className="flex-1">
                <h3 className="font-medium text-sm">团队协作</h3>
                <p className="text-xs text-gray-600">多角色协同工作，提升团队效率</p>
              </div>
            </div>
          </Card>

          <Card className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Shield className="h-5 w-5 text-purple-600" />
              </div>
              <div className="flex-1">
                <h3 className="font-medium text-sm">安全可靠</h3>
                <p className="text-xs text-gray-600">企业级安全保障和数据隔离</p>
              </div>
            </div>
          </Card>
        </div>

        {/* 底部信息 */}
        <div className="text-center text-xs text-gray-500 dark:text-gray-400">
          <p>© 2024 AI广告代投系统. All rights reserved.</p>
        </div>
      </div>
    </div>
  );
}