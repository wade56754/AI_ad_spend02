/**
 * Authentication hooks - 重导出
 *
 * 统一使用 features/auth/hooks/useAuth.ts
 * SoT Reference: AUTH_SPEC.md v2.0
 *
 * @deprecated 请直接从 '@/features/auth/hooks/useAuth' 导入
 */

export {
  useAuth,
  getAuthToken,
  setAuthToken,
  removeAuthToken,
} from '@/features/auth/hooks/useAuth';

// 类型重导出
export type {
  LoginRequest,
  User,
  AuthState,
} from '@/features/auth/types';
