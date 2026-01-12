/**
 * 格式化工具函数
 * @module lib/format
 */

import { format as dateFnsFormat, formatDistanceToNow } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import {
  CURRENCY_CODE,
  CURRENCY_LOCALE,
  DATE_FORMAT,
  DATETIME_FORMAT,
  TIME_FORMAT,
} from './constants';

/**
 * 货币格式化
 * @param amount 金额
 * @param showSymbol 是否显示货币符号
 * @returns 格式化后的货币字符串
 */
export function formatCurrency(amount: number, showSymbol = true): string {
  return new Intl.NumberFormat(CURRENCY_LOCALE, {
    style: showSymbol ? 'currency' : 'decimal',
    currency: CURRENCY_CODE,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
}

/**
 * 日期格式化
 * @param date 日期字符串或 Date 对象
 * @returns 格式化后的日期字符串 (yyyy-MM-dd)
 */
export function formatDate(date: string | Date | null | undefined): string {
  if (!date) return '-';
  try {
    return dateFnsFormat(new Date(date), DATE_FORMAT, { locale: zhCN });
  } catch {
    return '-';
  }
}

/**
 * 日期时间格式化
 * @param date 日期字符串或 Date 对象
 * @returns 格式化后的日期时间字符串 (yyyy-MM-dd HH:mm:ss)
 */
export function formatDateTime(date: string | Date | null | undefined): string {
  if (!date) return '-';
  try {
    return dateFnsFormat(new Date(date), DATETIME_FORMAT, { locale: zhCN });
  } catch {
    return '-';
  }
}

/**
 * 时间格式化
 * @param date 日期字符串或 Date 对象
 * @returns 格式化后的时间字符串 (HH:mm:ss)
 */
export function formatTime(date: string | Date | null | undefined): string {
  if (!date) return '-';
  try {
    return dateFnsFormat(new Date(date), TIME_FORMAT, { locale: zhCN });
  } catch {
    return '-';
  }
}

/**
 * 相对时间格式化
 * @param date 日期字符串或 Date 对象
 * @returns 相对时间字符串 (如: 3 分钟前)
 */
export function formatRelativeTime(date: string | Date | null | undefined): string {
  if (!date) return '-';
  try {
    return formatDistanceToNow(new Date(date), { addSuffix: true, locale: zhCN });
  } catch {
    return '-';
  }
}

/**
 * 百分比格式化
 * @param value 数值 (0-1 或 0-100)
 * @param decimals 小数位数
 * @param isDecimal 是否为小数格式 (0-1)
 * @returns 格式化后的百分比字符串
 */
export function formatPercent(value: number, decimals = 2, isDecimal = true): string {
  const percent = isDecimal ? value * 100 : value;
  return `${percent.toFixed(decimals)}%`;
}

/**
 * 数字格式化 (千分位)
 * @param value 数值
 * @param decimals 小数位数
 * @returns 格式化后的数字字符串
 */
export function formatNumber(value: number, decimals?: number): string {
  return new Intl.NumberFormat(CURRENCY_LOCALE, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
}

/**
 * 文件大小格式化
 * @param bytes 字节数
 * @returns 格式化后的文件大小字符串
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
}

/**
 * 手机号脱敏
 * @param phone 手机号
 * @returns 脱敏后的手机号
 */
export function maskPhone(phone: string): string {
  if (!phone || phone.length < 7) return phone;
  return phone.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2');
}

/**
 * 邮箱脱敏
 * @param email 邮箱
 * @returns 脱敏后的邮箱
 */
export function maskEmail(email: string): string {
  if (!email || !email.includes('@')) return email;
  const [name, domain] = email.split('@');
  const maskedName = name.length > 2 ? `${name[0]}***${name[name.length - 1]}` : '***';
  return `${maskedName}@${domain}`;
}

/**
 * 截断文本
 * @param text 文本
 * @param maxLength 最大长度
 * @param suffix 后缀
 * @returns 截断后的文本
 */
export function truncate(text: string, maxLength: number, suffix = '...'): string {
  if (!text || text.length <= maxLength) return text;
  return `${text.slice(0, maxLength)}${suffix}`;
}
