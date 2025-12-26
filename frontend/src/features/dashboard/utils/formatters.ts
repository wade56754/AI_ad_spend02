/**
 * Dashboard Formatting Utilities
 *
 * SoT: docs/3.dev-guides/DASHBOARD_LAYOUT_SPEC.md §5.2, §5.3
 *
 * 统一的数值格式化工具
 * - 金额格式化（千分位、万单位）
 * - CPL 格式化（边界场景处理）
 * - 百分比格式化
 * - 数字缩写
 */

/**
 * 安全地转换为数字
 */
export function safeNumber(value: number | undefined | null): number {
  const num = Number(value);
  return isNaN(num) ? 0 : num;
}

/**
 * 格式化 CPL - 处理边界场景
 * SoT: DASHBOARD_LAYOUT_SPEC.md §5.2
 *
 * @param spend 消耗金额
 * @param conversions 转化数
 * @returns 格式化后的 CPL，如 "¥39.36" 或 "--"
 */
export function formatCPL(spend: number | undefined | null, conversions: number | undefined | null): string {
  const s = safeNumber(spend);
  const c = safeNumber(conversions);

  if (c === 0) {
    return '--';  // 零转化
  }
  if (c < 5) {
    return `¥${(s / c).toFixed(2)} (低量)`;  // 低量标记
  }
  return `¥${(s / c).toFixed(2)}`;
}

/**
 * 格式化金额 - 自动选择单位
 * SoT: DASHBOARD_LAYOUT_SPEC.md §5.3
 *
 * @param amount 金额
 * @returns 格式化后的金额，如 "¥12.5万" 或 "¥1.2k" 或 "¥123.45"
 */
export function formatAmount(amount: number | undefined | null): string {
  const num = safeNumber(amount);
  if (num >= 10000) {
    return `¥${(num / 10000).toFixed(1)}万`;
  }
  if (num >= 1000) {
    return `¥${(num / 1000).toFixed(1)}k`;
  }
  return `¥${num.toFixed(2)}`;
}

/**
 * 格式化金额 - 标准千分位格式
 * @param value 金额数值
 * @param decimals 小数位数，默认 2
 * @returns 格式化后的金额字符串，如 "¥123,456.78"
 */
export function formatCurrency(value: number | undefined | null, decimals: number = 2): string {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(safeNumber(value));
}

/**
 * 格式化金额 - 万单位
 * @param value 金额数值
 * @param showSymbol 是否显示货币符号
 * @returns 格式化后的金额字符串，如 "¥12.5 万" 或 "12.5 万"
 */
export function formatCurrencyWan(value: number | undefined | null, showSymbol: boolean = true): string {
  const num = safeNumber(value);
  const wan = num / 10000;
  const symbol = showSymbol ? '¥' : '';

  if (wan >= 1000) {
    // 超过 1000 万，显示为 "¥1234.5 万"
    return `${symbol}${wan.toLocaleString('zh-CN', { minimumFractionDigits: 1, maximumFractionDigits: 1 })} 万`;
  } else if (wan >= 1) {
    // 1 万以上，显示为 "¥12.5 万"
    return `${symbol}${wan.toFixed(1)} 万`;
  } else {
    // 不足 1 万，显示标准格式
    return formatCurrency(num, 0);
  }
}

/**
 * 格式化金额 - 自动单位（用于图表 Y 轴）
 * @param value 金额数值
 * @returns 简洁格式，如 "¥12.5万" 或 "¥1234"
 */
export function formatCurrencyCompact(value: number | undefined | null): string {
  const num = safeNumber(value);
  if (num >= 10000) {
    return `¥${(num / 10000).toFixed(1)}万`;
  } else if (num >= 1000) {
    return `¥${(num / 1000).toFixed(1)}k`;
  } else {
    return `¥${num.toFixed(0)}`;
  }
}

/**
 * 格式化数字 - 千分位
 * @param value 数字
 * @returns 格式化后的字符串，如 "12,345"
 */
export function formatNumber(value: number | undefined | null): string {
  return safeNumber(value).toLocaleString('zh-CN');
}

/**
 * 格式化数字 - 简洁格式（用于图表）
 * @param value 数字
 * @returns 简洁格式，如 "12.5k" 或 "1.2M"
 */
export function formatNumberCompact(value: number | undefined | null): string {
  const num = safeNumber(value);
  if (num >= 1000000) {
    return `${(num / 1000000).toFixed(1)}M`;
  } else if (num >= 1000) {
    return `${(num / 1000).toFixed(1)}k`;
  } else {
    return num.toFixed(0);
  }
}

/**
 * 格式化百分比
 * @param value 百分比数值（如 12.5 表示 12.5%）
 * @param decimals 小数位数，默认 1
 * @param showSign 是否显示正负号
 * @returns 格式化后的百分比字符串，如 "+12.5%"
 */
export function formatPercent(
  value: number | undefined | null,
  decimals: number = 1,
  showSign: boolean = true
): string {
  const num = safeNumber(value);
  const sign = showSign && num > 0 ? '+' : '';
  return `${sign}${num.toFixed(decimals)}%`;
}

/**
 * 格式化变化率文案
 * @param change 变化百分比
 * @param compareText 对比文案，如 "较昨日"
 * @returns 完整文案，如 "较昨日 +12.5%"
 */
export function formatChangeText(change: number | undefined | null, compareText: string = '较昨日'): string {
  return `${compareText} ${formatPercent(change)}`;
}

/**
 * 格式化日期范围文案
 * @param preset 日期预设
 * @returns 中文文案，如 "今日"、"近 7 天"
 */
export function formatDateRangeText(preset: string): string {
  const labels: Record<string, string> = {
    today: '今日',
    '7d': '近 7 天',
    '30d': '近 30 天',
    custom: '自定义',
  };
  return labels[preset] || preset;
}
