/**
 * AI广告代投系统 - UI组件示例代码集
 *
 * 本文件包含了基于设计系统的核心组件实现示例
 * 展示了TypeScript、React、和CSS自定义属性的最佳实践
 *
 * 版本: v2.0
 * 更新日期: 2024-11-13
 */

import React, { useState, useEffect, forwardRef, ReactNode, ButtonHTMLAttributes, InputHTMLAttributes } from 'react';

// ===== 类型定义 =====

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';
export type ButtonSize = 'sm' | 'md' | 'lg' | 'xl';
export type Theme = 'light' | 'dark';
export type StatusType = 'success' | 'warning' | 'error' | 'info' | 'pending';

export interface ButtonProps extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'size'> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  fullWidth?: boolean;
  icon?: ReactNode;
  iconPosition?: 'left' | 'right';
  children: ReactNode;
}

export interface MetricCardProps {
  title: string;
  value: string | number;
  change?: number;
  changeType?: 'up' | 'down' | 'neutral';
  icon?: ReactNode;
  trend?: 'up' | 'down' | 'neutral';
  color?: 'primary' | 'success' | 'warning' | 'error';
  loading?: boolean;
  description?: string;
}

export interface StatusBadgeProps {
  status: StatusType;
  children: ReactNode;
  dot?: boolean;
  size?: 'sm' | 'md';
}

export interface FormInputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'size'> {
  label?: string;
  error?: string;
  hint?: string;
  size?: 'sm' | 'md' | 'lg';
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
  success?: boolean;
}

export interface ModalProps {
  open: boolean;
  onClose: () => void;
  title?: ReactNode;
  footer?: ReactNode;
  width?: number;
  closable?: boolean;
  maskClosable?: boolean;
  centered?: boolean;
  children: ReactNode;
}

// ===== 工具函数 =====

/**
 * 格式化数值显示
 */
export const formatNumber = (num: number | string): string => {
  const n = typeof num === 'string' ? parseFloat(num) : num;
  if (isNaN(n)) return '0';

  if (n >= 1000000) {
    return `${(n / 1000000).toFixed(1)}M`;
  } else if (n >= 1000) {
    return `${(n / 1000).toFixed(1)}K`;
  }
  return n.toFixed(0);
};

/**
 * 格式化百分比变化
 */
export const formatChange = (change: number): string => {
  const sign = change > 0 ? '+' : '';
  return `${sign}${change.toFixed(1)}%`;
};

/**
 * 生成唯一ID
 */
export const generateId = (prefix: string = 'id'): string => {
  return `${prefix}-${Math.random().toString(36).substr(2, 9)}`;
};

// ===== 主题管理 =====

/**
 * 主题切换Hook
 */
export const useTheme = () => {
  const [theme, setTheme] = useState<Theme>('dark');

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  };

  // 保存到localStorage
  useEffect(() => {
    localStorage.setItem('theme', theme);
  }, [theme]);

  // 从localStorage恢复
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') as Theme;
    if (savedTheme) {
      setTheme(savedTheme);
    }
  }, []);

  // 应用主题到DOM
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  return { theme, toggleTheme, setTheme };
};

// ===== 组件实现 =====

/**
 * 按钮组件 - 完整实现
 *
 * 支持多种变体、尺寸、状态和图标
 * 符合WCAG 2.1 AA级可访问性标准
 */
export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({
    variant = 'primary',
    size = 'md',
    loading = false,
    disabled = false,
    fullWidth = false,
    icon,
    iconPosition = 'left',
    children,
    className = '',
    onClick,
    ...props
  }, ref) => {
    const [isPressed, setIsPressed] = useState(false);

    const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
      if (loading || disabled) return;
      onClick?.(e);
    };

    const handleMouseDown = () => setIsPressed(true);
    const handleMouseUp = () => setIsPressed(false);
    const handleMouseLeave = () => setIsPressed(false);

    const baseClasses = 'btn inline-flex items-center justify-center font-medium transition-all duration-200 focus-visible:outline-none disabled:cursor-not-allowed';

    const variantClasses = {
      primary: 'btn-primary text-white border-0',
      secondary: 'btn-secondary bg-transparent border-2',
      ghost: 'btn-ghost bg-transparent border-0',
      danger: 'btn-danger bg-gradient-to-r from-red-500 to-red-600 text-white border-0 hover:from-red-600 hover:to-red-700',
    };

    const sizeClasses = {
      sm: 'btn-sm px-3 py-1.5 text-xs',
      md: 'btn-md px-6 py-3 text-sm',
      lg: 'btn-lg px-8 py-4 text-base',
      xl: 'btn-xl px-10 py-5 text-lg',
    };

    const stateClasses = loading
      ? 'opacity-70 pointer-events-none'
      : disabled
      ? 'opacity-50 cursor-not-allowed'
      : isPressed
      ? 'transform scale-95'
      : 'hover:scale-105';

    const widthClass = fullWidth ? 'w-full' : '';

    const classes = [
      baseClasses,
      variantClasses[variant],
      sizeClasses[size],
      stateClasses,
      widthClass,
      className
    ].filter(Boolean).join(' ');

    const renderIcon = () => {
      if (!icon) return null;
      return (
        <span className={`flex items-center ${iconPosition === 'right' ? 'ml-2' : 'mr-2'}`}>
          {icon}
        </span>
      );
    };

    return (
      <button
        ref={ref}
        className={classes}
        disabled={disabled || loading}
        onClick={handleClick}
        onMouseDown={handleMouseDown}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseLeave}
        {...props}
      >
        {loading && (
          <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-current" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
        )}
        {iconPosition === 'left' && renderIcon()}
        <span className={loading ? 'opacity-0' : ''}>{children}</span>
        {iconPosition === 'right' && renderIcon()}
      </button>
    );
  }
);

Button.displayName = 'Button';

/**
 * 指标卡片组件
 *
 * 显示关键业务指标，支持趋势变化和加载状态
 */
export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  change,
  changeType = 'neutral',
  icon,
  trend = 'neutral',
  color = 'primary',
  loading = false,
  description
}) => {
  const [isHovered, setIsHovered] = useState(false);

  const colorClasses = {
    primary: 'metric-card-primary',
    success: 'metric-card-success',
    warning: 'metric-card-warning',
    error: 'metric-card-error',
  };

  const getTrendIcon = () => {
    switch (trend) {
      case 'up':
        return <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
        </svg>;
      case 'down':
        return <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
        </svg>;
      default:
        return null;
    }
  };

  const getChangeColor = () => {
    if (changeType === 'up') return 'text-green-500';
    if (changeType === 'down') return 'text-red-500';
    return 'text-gray-500';
  };

  if (loading) {
    return (
      <div className="metric-card animate-pulse">
        <div className="flex items-center justify-between mb-4">
          <div className="w-8 h-8 bg-gray-600 rounded-lg"></div>
          <div className="w-16 h-4 bg-gray-600 rounded"></div>
        </div>
        <div className="w-24 h-8 bg-gray-600 rounded mb-2"></div>
        <div className="w-32 h-4 bg-gray-600 rounded"></div>
      </div>
    );
  }

  return (
    <div
      className={`metric-card ${colorClasses[color]} cursor-pointer transform transition-all duration-300 ${isHovered ? 'scale-105 -translate-y-1' : ''}`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className="flex items-center justify-between mb-4">
        <div className="p-2 bg-white bg-opacity-10 rounded-lg">
          {icon}
        </div>
        {change !== undefined && (
          <div className={`flex items-center text-sm font-medium ${getChangeColor()}`}>
            {getTrendIcon()}
            <span className="ml-1">{formatChange(change)}</span>
          </div>
        )}
      </div>

      <div className="space-y-1">
        <h3 className="text-2xl font-bold text-white">
          {formatNumber(value)}
        </h3>
        <p className="text-sm text-gray-300">{title}</p>
        {description && (
          <p className="text-xs text-gray-400 mt-2">{description}</p>
        )}
      </div>
    </div>
  );
};

/**
 * 状态标签组件
 */
export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  children,
  dot = true,
  size = 'md'
}) => {
  const statusClasses = {
    success: 'bg-green-100 text-green-800 border-green-200',
    warning: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    error: 'bg-red-100 text-red-800 border-red-200',
    info: 'bg-blue-100 text-blue-800 border-blue-200',
    pending: 'bg-gray-100 text-gray-800 border-gray-200',
  };

  const sizeClasses = {
    sm: 'px-2 py-1 text-xs',
    md: 'px-3 py-1.5 text-sm',
  };

  return (
    <span className={`status-badge inline-flex items-center rounded-full border font-medium ${statusClasses[status]} ${sizeClasses[size]}`}>
      {dot && (
        <span className={`status-badge-dot w-2 h-2 rounded-full bg-current mr-2 ${status}`}></span>
      )}
      {children}
    </span>
  );
};

/**
 * 表单输入组件
 */
export const FormInput: React.FC<FormInputProps> = ({
  label,
  error,
  hint,
  size = 'md',
  leftIcon,
  rightIcon,
  success = false,
  className = '',
  id,
  ...props
}) => {
  const [focused, setFocused] = useState(false);
  const inputId = id || generateId('input');

  const sizeClasses = {
    sm: 'px-3 py-2 text-sm',
    md: 'px-4 py-3 text-base',
    lg: 'px-5 py-4 text-lg',
  };

  const stateClasses = error
    ? 'border-red-500 focus:border-red-500 focus:ring-red-500'
    : success
    ? 'border-green-500 focus:border-green-500 focus:ring-green-500'
    : focused
    ? 'border-blue-500 focus:border-blue-500 focus:ring-blue-500'
    : 'border-gray-300 focus:border-blue-500 focus:ring-blue-500';

  return (
    <div className="form-field">
      {label && (
        <label htmlFor={inputId} className="form-label block text-sm font-medium text-gray-700 mb-2">
          {label}
        </label>
      )}

      <div className="relative">
        {leftIcon && (
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            {leftIcon}
          </div>
        )}

        <input
          id={inputId}
          className={`form-input block w-full rounded-lg border border-gray-300 bg-white shadow-sm transition-colors ${sizeClasses[size]} ${stateClasses} ${leftIcon ? 'pl-10' : ''} ${rightIcon ? 'pr-10' : ''} ${className}`}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          {...props}
        />

        {rightIcon && (
          <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
            {rightIcon}
          </div>
        )}
      </div>

      {hint && !error && (
        <p className="form-hint mt-1 text-sm text-gray-500">{hint}</p>
      )}

      {error && (
        <p className="form-error mt-1 text-sm text-red-600">{error}</p>
      )}
    </div>
  );
};

/**
 * 模态框组件
 */
export const Modal: React.FC<ModalProps> = ({
  open,
  onClose,
  title,
  footer,
  width = 600,
  closable = true,
  maskClosable = true,
  centered = false,
  children
}) => {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    setVisible(open);
  }, [open]);

  const handleMaskClick = () => {
    if (maskClosable) {
      onClose();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      onClose();
    }
  };

  if (!visible) return null;

  return (
    <div
      className="modal-overlay fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      onClick={handleMaskClick}
      onKeyDown={handleKeyDown}
      tabIndex={-1}
    >
      <div
        className="modal-content bg-white rounded-xl shadow-2xl max-w-full mx-4"
        style={{ width: `${width}px` }}
        onClick={(e) => e.stopPropagation()}
      >
        {(title || closable) && (
          <div className="modal-header flex items-center justify-between p-6 border-b border-gray-200">
            {title && (
              <h2 className="modal-title text-xl font-semibold text-gray-900">{title}</h2>
            )}
            {closable && (
              <button
                type="button"
                className="modal-close p-2 hover:bg-gray-100 rounded-lg transition-colors"
                onClick={onClose}
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
        )}

        <div className="modal-body p-6">
          {children}
        </div>

        {footer && (
          <div className="modal-footer p-6 border-t border-gray-200 flex justify-end space-x-3">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
};

// ===== 组合组件示例 =====

/**
 * 主题切换按钮
 */
export const ThemeToggle: React.FC = () => {
  const { theme, toggleTheme } = useTheme();

  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={toggleTheme}
      icon={
        theme === 'dark' ? (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
          </svg>
        ) : (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
          </svg>
        )
      }
    >
      {theme === 'dark' ? '浅色模式' : '深色模式'}
    </Button>
  );
};

/**
 * 数据表格演示组件
 */
interface DataTableRow {
  id: string;
  name: string;
  status: StatusType;
  budget: number;
  spent: number;
  roi: number;
  lastUpdated: string;
}

export const DataTableDemo: React.FC = () => {
  const [data, setData] = useState<DataTableRow[]>([
    {
      id: '1',
      name: 'Facebook广告活动A',
      status: 'success',
      budget: 10000,
      spent: 7800,
      roi: 12.5,
      lastUpdated: '2024-11-13'
    },
    {
      id: '2',
      name: 'Instagram品牌推广',
      status: 'warning',
      budget: 5000,
      spent: 4500,
      roi: 8.2,
      lastUpdated: '2024-11-12'
    },
    {
      id: '3',
      name: 'TikTok内容营销',
      status: 'pending',
      budget: 8000,
      spent: 3200,
      roi: 15.8,
      lastUpdated: '2024-11-13'
    },
  ]);

  const [sortConfig, setSortConfig] = useState<{
    key: keyof DataTableRow | null;
    direction: 'asc' | 'desc';
  }>({ key: null, direction: 'asc' });

  const handleSort = (key: keyof DataTableRow) => {
    let direction: 'asc' | 'desc' = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });

    const sortedData = [...data].sort((a, b) => {
      if (a[key] === null || a[key] === undefined) return 1;
      if (b[key] === null || b[key] === undefined) return -1;

      if (a[key]! < b[key]!) return direction === 'asc' ? -1 : 1;
      if (a[key]! > b[key]!) return direction === 'asc' ? 1 : -1;
      return 0;
    });

    setData(sortedData);
  };

  return (
    <div className="data-table-container bg-white rounded-xl shadow-lg overflow-hidden">
      <div className="overflow-x-auto">
        <table className="data-table w-full">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('name')}>
                <div className="flex items-center space-x-1">
                  <span>项目名称</span>
                  {sortConfig.key === 'name' && (
                    <span>{sortConfig.direction === 'asc' ? '↑' : '↓'}</span>
                  )}
                </div>
              </th>
              <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                状态
              </th>
              <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('budget')}>
                <div className="flex items-center space-x-1">
                  <span>预算</span>
                  {sortConfig.key === 'budget' && (
                    <span>{sortConfig.direction === 'asc' ? '↑' : '↓'}</span>
                  )}
                </div>
              </th>
              <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('spent')}>
                <div className="flex items-center space-x-1">
                  <span>已花费</span>
                  {sortConfig.key === 'spent' && (
                    <span>{sortConfig.direction === 'asc' ? '↑' : '↓'}</span>
                  )}
                </div>
              </th>
              <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('roi')}>
                <div className="flex items-center space-x-1">
                  <span>ROI</span>
                  {sortConfig.key === 'roi' && (
                    <span>{sortConfig.direction === 'asc' ? '↑' : '↓'}</span>
                  )}
                </div>
              </th>
              <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                更新时间
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {data.map((row) => (
              <tr key={row.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-gray-900">{row.name}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <StatusBadge status={row.status} size="sm">
                    {row.status === 'success' && '运行中'}
                    {row.status === 'warning' && '需关注'}
                    {row.status === 'pending' && '等待中'}
                  </StatusBadge>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">${formatNumber(row.budget)}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">${formatNumber(row.spent)}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className={`text-sm font-medium ${
                    row.roi > 10 ? 'text-green-600' :
                    row.roi > 5 ? 'text-yellow-600' : 'text-red-600'
                  }`}>
                    {row.roi.toFixed(1)}%
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-500">{row.lastUpdated}</div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// ===== 使用示例 =====

/**
 * 完整的仪表板示例组件
 */
export const DashboardExample: React.FC = () => {
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    budget: '',
    description: ''
  });

  return (
    <div className="min-h-screen bg-gray-50" data-theme="light">
      {/* 头部导航 */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900">AI广告代投系统</h1>
            </div>
            <div className="flex items-center space-x-4">
              <ThemeToggle />
              <Button variant="primary" onClick={() => setShowModal(true)}>
                创建项目
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* 主要内容 */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 指标卡片区域 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <MetricCard
            title="总预算"
            value={125000}
            change={12.5}
            changeType="up"
            trend="up"
            color="primary"
            icon={
              <svg className="w-6 h-6 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            }
            description="本月广告总预算"
          />

          <MetricCard
            title="活跃项目"
            value={24}
            change={8.2}
            changeType="up"
            trend="up"
            color="success"
            icon={
              <svg className="w-6 h-6 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
            }
            description="当前运行中的项目"
          />

          <MetricCard
            title="转化率"
            value={3.8}
            change={-2.1}
            changeType="down"
            trend="down"
            color="warning"
            icon={
              <svg className="w-6 h-6 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            }
            description="平均转化率百分比"
          />

          <MetricCard
            title="ROI"
            value={15.2}
            change={5.4}
            changeType="up"
            trend="up"
            color="error"
            icon={
              <svg className="w-6 h-6 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            }
            description="投资回报率"
          />
        </div>

        {/* 数据表格 */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-lg font-semibold text-gray-900">项目列表</h2>
            <Button variant="secondary" size="sm">
              导出报告
            </Button>
          </div>

          <DataTableDemo />
        </div>
      </main>

      {/* 创建项目模态框 */}
      <Modal
        open={showModal}
        onClose={() => setShowModal(false)}
        title="创建新项目"
        width={600}
        footer={
          <>
            <Button variant="ghost" onClick={() => setShowModal(false)}>
              取消
            </Button>
            <Button variant="primary" onClick={() => setShowModal(false)}>
              创建项目
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <FormInput
            label="项目名称"
            placeholder="请输入项目名称"
            value={formData.name}
            onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
            leftIcon={
              <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
            }
          />

          <FormInput
            label="项目预算"
            type="number"
            placeholder="请输入项目预算"
            value={formData.budget}
            onChange={(e) => setFormData(prev => ({ ...prev, budget: e.target.value }))}
            leftIcon={
              <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            }
          />

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              项目描述
            </label>
            <textarea
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              rows={4}
              placeholder="请输入项目描述..."
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
            />
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default DashboardExample;