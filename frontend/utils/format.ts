/**
 * 格式化工具函数
 * 提供统一的数值、货币、百分比等格式化功能
 */

/**
 * 格式化数值显示
 * 支持千分位分隔和单位简化
 */
export const formatNumber = (num: number | string, options: {
  compact?: boolean;
  decimals?: number;
  separator?: string;
} = {}): string => {
  const { compact = false, decimals = 0, separator = ',' } = options;

  const n = typeof num === 'string' ? parseFloat(num) : num;
  if (isNaN(n)) return '0';

  // 紧凑模式（K/M/B）
  if (compact) {
    if (n >= 1000000000) {
      return `${(n / 1000000000).toFixed(1)}B`;
    } else if (n >= 1000000) {
      return `${(n / 1000000).toFixed(1)}M`;
    } else if (n >= 1000) {
      return `${(n / 1000).toFixed(1)}K`;
    }
  }

  // 标准格式化
  const formatted = n.toLocaleString('zh-CN', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
    useGrouping: true
  });

  // 替换默认分隔符（如果需要）
  if (separator !== ',') {
    return formatted.replace(/,/g, separator);
  }

  return formatted;
};

/**
 * 格式化货币
 * 支持人民币格式化
 */
export const formatCurrency = (amount: number | string, options: {
  currency?: string;
  showSymbol?: boolean;
  compact?: boolean;
} = {}): string => {
  const { currency = 'CNY', showSymbol = true, compact = false } = options;

  const amountNum = typeof amount === 'string' ? parseFloat(amount) : amount;
  if (isNaN(amountNum)) return '￥0';

  // 紧凑模式
  if (compact && amountNum >= 10000) {
    const formatted = formatNumber(amountNum, { compact: true, decimals: 1 });
    return showSymbol ? `￥${formatted}` : formatted;
  }

  // 标准货币格式
  const formatted = amountNum.toLocaleString('zh-CN', {
    style: showSymbol ? 'currency' : 'decimal',
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });

  return formatted;
};

/**
 * 格式化百分比变化
 */
export const formatChange = (change: number, options: {
  showSign?: boolean;
  decimals?: number;
} = {}): string => {
  const { showSign = true, decimals = 1 } = options;

  const sign = change > 0 && showSign ? '+' : '';
  return `${sign}${change.toFixed(decimals)}%`;
};

/**
 * 格式化时间
 */
export const formatTime = (date: Date | string | number, options: {
  relative?: boolean;
  format?: string;
} = {}): string => {
  const { relative = false, format = 'default' } = options;

  const dateObj = typeof date === 'string' || typeof date === 'number'
    ? new Date(date)
    : date;

  if (isNaN(dateObj.getTime())) return '无效时间';

  // 相对时间
  if (relative) {
    const now = new Date();
    const diff = now.getTime() - dateObj.getTime();
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) return `${days}天前`;
    if (hours > 0) return `${hours}小时前`;
    if (minutes > 0) return `${minutes}分钟前`;
    return '刚刚';
  }

  // 绝对时间格式
  switch (format) {
    case 'short':
      return dateObj.toLocaleDateString('zh-CN');
    case 'long':
      return dateObj.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    case 'time':
      return dateObj.toLocaleTimeString('zh-CN');
    default:
      return dateObj.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
      });
  }
};

/**
 * 格式化文件大小
 */
export const formatFileSize = (bytes: number, decimals = 1): string => {
  if (bytes === 0) return '0 B';

  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];

  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
};

/**
 * 格式化时长（秒转换为时分秒）
 */
export const formatDuration = (seconds: number, options: {
  showHours?: boolean;
  showMinutes?: boolean;
  showSeconds?: boolean;
} = {}): string => {
  const { showHours = true, showMinutes = true, showSeconds = true } = options;

  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainingSeconds = seconds % 60;

  const parts = [];

  if (showHours && hours > 0) {
    parts.push(`${hours}小时`);
  }

  if (showMinutes && (hours > 0 || minutes > 0)) {
    parts.push(`${minutes}分钟`);
  }

  if (showSeconds) {
    parts.push(`${remainingSeconds}秒`);
  }

  return parts.join('');
};

/**
 * 截断文本
 */
export const truncateText = (text: string, maxLength: number, suffix = '...'): string => {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength - suffix.length) + suffix;
};

/**
 * 生成唯一ID
 */
export const generateId = (prefix = 'id'): string => {
  return `${prefix}-${Math.random().toString(36).substr(2, 9)}`;
};

/**
 * 防抖函数
 */
export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) => {
  let timeout: NodeJS.Timeout;

  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
};

/**
 * 节流函数
 */
export const throttle = <T extends (...args: any[]) => any>(
  func: T,
  limit: number
): ((...args: Parameters<T>) => void) => {
  let inThrottle: boolean;

  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
};