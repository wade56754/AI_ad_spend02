/**
 * 金额安全计算工具
 *
 * 解决问题: FE-P0-2 - 金额浮点相减精度丢失
 * SoT: MASTER.md v4.9 - 资金计算必须保持精度
 *
 * 使用示例:
 *   import { moneySubtract, safeAverage } from '@/lib/money';
 *
 *   // 替代 totalTopup - totalSpend 可能的浮点误差
 *   const balance = moneySubtract(totalTopup, totalSpend);
 *
 *   // 替代 values.reduce(...) / 7 的固定除数问题
 *   const avg = safeAverage(values);
 *
 * @module lib/money
 */

/**
 * 将数值四舍五入到指定小数位
 * 使用整数运算避免浮点误差
 */
function roundTo(value: number, decimals: number = 2): number {
  const factor = Math.pow(10, decimals);
  return Math.round(value * factor) / factor;
}

/**
 * 安全相加金额
 *
 * @param values - 要相加的金额数组
 * @returns 四舍五入到 2 位小数的和
 *
 * @example
 * moneyAdd(100.1, 50.25, 0.05) // 150.40
 */
export function moneyAdd(...values: (number | null | undefined)[]): number {
  const sum = values.reduce<number>((acc, v) => acc + (v ?? 0), 0);
  return roundTo(sum);
}

/**
 * 安全相减金额
 * 使用整数运算避免浮点误差
 *
 * @param a - 被减数
 * @param b - 减数
 * @returns 四舍五入到 2 位小数的差
 *
 * @example
 * moneySubtract(100.1, 0.1) // 100.00 (而非 99.99999...)
 * moneySubtract(1000.00, 300.50) // 699.50
 */
export function moneySubtract(
  a: number | null | undefined,
  b: number | null | undefined
): number {
  // 使用整数运算：先乘以 100，计算后再除以 100
  const aInt = Math.round((a ?? 0) * 100);
  const bInt = Math.round((b ?? 0) * 100);
  return (aInt - bInt) / 100;
}

/**
 * 安全相乘金额
 *
 * @param amount - 金额
 * @param factor - 乘数
 * @returns 四舍五入到 2 位小数的积
 *
 * @example
 * moneyMultiply(100.00, 1.05) // 105.00
 */
export function moneyMultiply(
  amount: number | null | undefined,
  factor: number | null | undefined
): number {
  return roundTo((amount ?? 0) * (factor ?? 0));
}

/**
 * 安全除法，处理除零情况
 *
 * @param amount - 被除数
 * @param divisor - 除数
 * @param defaultValue - 除数为零时的默认值
 * @returns 四舍五入到 2 位小数的商
 *
 * @example
 * moneyDivide(100.00, 3) // 33.33
 * moneyDivide(100.00, 0) // 0
 */
export function moneyDivide(
  amount: number | null | undefined,
  divisor: number | null | undefined,
  defaultValue: number = 0
): number {
  const d = divisor ?? 0;
  if (d === 0) return defaultValue;
  return roundTo((amount ?? 0) / d);
}

/**
 * 安全计算平均值
 * 解决 FE-P0-1: 7日均值固定除以7的问题
 *
 * @param values - 值数组
 * @param defaultValue - 数组为空时的默认值
 * @returns 四舍五入到 2 位小数的平均值
 *
 * @example
 * safeAverage([10, 20, 30]) // 20.00
 * safeAverage([]) // 0
 * safeAverage([100, 200], -1) // 150.00
 */
export function safeAverage(
  values: (number | null | undefined)[],
  defaultValue: number = 0
): number {
  const validValues = values.filter((v): v is number => v != null);
  if (validValues.length === 0) return defaultValue;

  const sum = validValues.reduce((acc, v) => acc + v, 0);
  return roundTo(sum / validValues.length);
}

/**
 * 计算百分比
 *
 * @param part - 部分值
 * @param total - 总值
 * @param defaultValue - 总值为零时的默认值
 * @returns 百分比值 (0-100)
 *
 * @example
 * calculatePercentage(25, 100) // 25.00
 * calculatePercentage(1, 3) // 33.33
 * calculatePercentage(50, 0) // 0
 */
export function calculatePercentage(
  part: number | null | undefined,
  total: number | null | undefined,
  defaultValue: number = 0
): number {
  const t = total ?? 0;
  if (t === 0) return defaultValue;
  return roundTo(((part ?? 0) / t) * 100);
}

/**
 * 计算增长率
 *
 * @param current - 当前值
 * @param previous - 之前值
 * @param defaultValue - 之前值为零时的默认值
 * @returns 增长率百分比 (可能为负)
 *
 * @example
 * calculateGrowthRate(120, 100) // 20.00
 * calculateGrowthRate(80, 100) // -20.00
 * calculateGrowthRate(100, 0) // 0
 */
export function calculateGrowthRate(
  current: number | null | undefined,
  previous: number | null | undefined,
  defaultValue: number = 0
): number {
  const prev = previous ?? 0;
  if (prev === 0) return defaultValue;
  return roundTo(((current ?? 0) - prev) / prev * 100);
}

/**
 * 格式化金额显示（带千分位）
 * 注意：这是显示用途，计算请使用上面的函数
 *
 * @param amount - 金额
 * @param decimals - 小数位数
 * @returns 格式化的字符串
 *
 * @example
 * formatMoney(1234567.89) // "1,234,567.89"
 */
export function formatMoney(
  amount: number | null | undefined,
  decimals: number = 2
): string {
  const value = amount ?? 0;
  return value.toLocaleString('zh-CN', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

/**
 * 确保金额为正数
 *
 * @param amount - 金额
 * @returns 非负金额
 *
 * @example
 * ensurePositive(-100) // 0
 * ensurePositive(100) // 100
 */
export function ensurePositive(amount: number | null | undefined): number {
  return Math.max(amount ?? 0, 0);
}

/**
 * 比较两个金额是否相等（考虑浮点误差）
 *
 * @param a - 金额 A
 * @param b - 金额 B
 * @param tolerance - 容差（默认 0.01）
 * @returns 是否相等
 *
 * @example
 * moneyEquals(100.00, 100.001) // true (在容差内)
 * moneyEquals(100.00, 100.02) // false
 */
export function moneyEquals(
  a: number | null | undefined,
  b: number | null | undefined,
  tolerance: number = 0.01
): boolean {
  return Math.abs((a ?? 0) - (b ?? 0)) < tolerance;
}
