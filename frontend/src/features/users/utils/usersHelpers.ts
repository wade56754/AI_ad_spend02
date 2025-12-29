/**
 * Users Helper Functions
 *
 * 从 UsersPage.tsx 提取的辅助函数
 */

import { USER_ROLE_OPTIONS, type UserRole } from '../types';

export function getRoleConfig(role: UserRole) {
  return USER_ROLE_OPTIONS.find((r) => r.value === role) || USER_ROLE_OPTIONS[4];
}

export function formatDate(dateString: string | null | undefined) {
  if (!dateString) return '-';
  return new Date(dateString).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function getRoleBadgeClass(color: string): string {
  const colorMap: Record<string, string> = {
    red: 'bg-red-100 text-red-700',
    green: 'bg-green-100 text-green-700',
    blue: 'bg-blue-100 text-blue-700',
    purple: 'bg-purple-100 text-purple-700',
    orange: 'bg-orange-100 text-orange-700',
  };
  return colorMap[color] || colorMap.orange;
}
