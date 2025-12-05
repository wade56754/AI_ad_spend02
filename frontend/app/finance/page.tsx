/**
 * 财务管理页面
 *
 * 对齐：FRONTEND_MODULE_SHELL_PATTERN v1.0
 * - page.tsx 仅作为编排层，挂载 Shell
 * - 所有业务逻辑在 src/modules/finance/ 中实现
 */

import { FinancePageShell } from '@/modules/finance';

export default function FinanceManagementPage() {
  return <FinancePageShell />;
}
