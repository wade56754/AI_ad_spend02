/**
 * Frontend Error Codes Mapping
 *
 * 与后端错误码对齐，提供用户友好的错误消息
 * SoT: ERROR_CODES_SOT.md v2.2
 *
 * @module lib/error-codes
 */

// ============================================================================
// Error Code Types
// ============================================================================

export interface ErrorCodeInfo {
  code: string;
  message: string;
  userMessage: string; // 面向用户的友好消息
  action?: string; // 建议用户采取的操作
}

// ============================================================================
// Error Code Categories
// ============================================================================

/**
 * 认证授权错误码 (AUTH_)
 */
export const AUTH_ERROR_CODES: Record<string, ErrorCodeInfo> = {
  AUTH_001: {
    code: 'AUTH_001',
    message: '用户名或密码错误',
    userMessage: '账号或密码不正确，请重新输入',
    action: '请检查您的账号和密码',
  },
  AUTH_002: {
    code: 'AUTH_002',
    message: '账户已被禁用',
    userMessage: '您的账户已被停用',
    action: '请联系管理员',
  },
  AUTH_003: {
    code: 'AUTH_003',
    message: '令牌已被撤销',
    userMessage: '登录已失效',
    action: '请重新登录',
  },
  AUTH_004: {
    code: 'AUTH_004',
    message: '用户不存在或已被禁用',
    userMessage: '用户不存在或已被停用',
    action: '请检查账号是否正确',
  },
  AUTH_100: {
    code: 'AUTH_100',
    message: '邮箱已被注册',
    userMessage: '该邮箱已被注册',
    action: '请使用其他邮箱或直接登录',
  },
  AUTH_400: {
    code: 'AUTH_400',
    message: '未提供认证令牌',
    userMessage: '请先登录',
    action: '请登录后再试',
  },
  AUTH_401: {
    code: 'AUTH_401',
    message: '无效的认证令牌',
    userMessage: '登录已失效',
    action: '请重新登录',
  },
  AUTH_402: {
    code: 'AUTH_402',
    message: '令牌已过期',
    userMessage: '登录已过期',
    action: '请重新登录',
  },
  AUTH_500: {
    code: 'AUTH_500',
    message: '权限不足',
    userMessage: '您没有权限执行此操作',
    action: '请联系管理员获取权限',
  },
  AUTH_501: {
    code: 'AUTH_501',
    message: '角色权限不足',
    userMessage: '您的角色没有此操作权限',
    action: '请联系管理员',
  },
};

/**
 * 业务逻辑错误码 (BIZ_)
 */
export const BIZ_ERROR_CODES: Record<string, ErrorCodeInfo> = {
  BIZ_001: {
    code: 'BIZ_001',
    message: '无效的操作',
    userMessage: '当前状态下无法执行此操作',
    action: '请检查操作条件',
  },
  BIZ_002: {
    code: 'BIZ_002',
    message: '资源不存在',
    userMessage: '找不到相关数据',
    action: '请刷新页面后重试',
  },
  BIZ_003: {
    code: 'BIZ_003',
    message: '资源已存在',
    userMessage: '该记录已存在',
    action: '请检查是否重复创建',
  },
  BIZ_100: {
    code: 'BIZ_100',
    message: '金额无效',
    userMessage: '请输入有效的金额',
    action: '金额必须大于0',
  },
  BIZ_101: {
    code: 'BIZ_101',
    message: '余额不足',
    userMessage: '账户余额不足',
    action: '请先充值',
  },
  BIZ_200: {
    code: 'BIZ_200',
    message: '日期范围无效',
    userMessage: '开始日期不能晚于结束日期',
    action: '请检查日期范围',
  },
  BIZ_201: {
    code: 'BIZ_201',
    message: '日期不能为未来',
    userMessage: '日期不能是未来日期',
    action: '请选择今天或之前的日期',
  },
  BIZ_300: {
    code: 'BIZ_300',
    message: '状态无效',
    userMessage: '无效的状态值',
    action: '请刷新页面后重试',
  },
  BIZ_301: {
    code: 'BIZ_301',
    message: '状态转换不允许',
    userMessage: '当前状态不允许此操作',
    action: '请检查当前状态',
  },
  BIZ_600: {
    code: 'BIZ_600',
    message: '账本创建失败',
    userMessage: '账本记录创建失败',
    action: '请稍后重试',
  },
  BIZ_601: {
    code: 'BIZ_601',
    message: '账本查询失败',
    userMessage: '账本查询失败',
    action: '请稍后重试',
  },
  BIZ_602: {
    code: 'BIZ_602',
    message: '交易记录不存在',
    userMessage: '找不到该交易记录',
    action: '请检查交易ID',
  },
};

/**
 * 参数验证错误码 (VALIDATION_)
 */
export const VALIDATION_ERROR_CODES: Record<string, ErrorCodeInfo> = {
  VALIDATION_001: {
    code: 'VALIDATION_001',
    message: '必填字段缺失',
    userMessage: '请填写所有必填项',
    action: '请检查表单中的必填项',
  },
  VALIDATION_002: {
    code: 'VALIDATION_002',
    message: '格式无效',
    userMessage: '输入格式不正确',
    action: '请检查输入格式',
  },
  VALIDATION_003: {
    code: 'VALIDATION_003',
    message: '邮箱格式无效',
    userMessage: '邮箱格式不正确',
    action: '请输入有效的邮箱地址',
  },
  VALIDATION_004: {
    code: 'VALIDATION_004',
    message: '电话格式无效',
    userMessage: '电话号码格式不正确',
    action: '请输入有效的电话号码',
  },
  VALIDATION_005: {
    code: 'VALIDATION_005',
    message: '值超出范围',
    userMessage: '输入值超出允许范围',
    action: '请检查输入值的范围',
  },
};

/**
 * 系统错误码 (SYS_)
 */
export const SYS_ERROR_CODES: Record<string, ErrorCodeInfo> = {
  SYS_001: {
    code: 'SYS_001',
    message: '系统内部错误',
    userMessage: '系统出现问题',
    action: '请稍后重试，如问题持续请联系管理员',
  },
  SYS_002: {
    code: 'SYS_002',
    message: '服务暂时不可用',
    userMessage: '服务暂时不可用',
    action: '请稍后重试',
  },
  SYS_003: {
    code: 'SYS_003',
    message: '请求超时',
    userMessage: '请求超时',
    action: '请检查网络后重试',
  },
  SYS_004: {
    code: 'SYS_004',
    message: '请求过于频繁',
    userMessage: '请求过于频繁',
    action: '请稍后再试',
  },
};

/**
 * 数据库错误码 (DB_)
 */
export const DB_ERROR_CODES: Record<string, ErrorCodeInfo> = {
  DB_001: {
    code: 'DB_001',
    message: '数据库连接失败',
    userMessage: '服务暂时不可用',
    action: '请稍后重试',
  },
  DB_004: {
    code: 'DB_004',
    message: '唯一性约束违反',
    userMessage: '该记录已存在',
    action: '请检查是否重复',
  },
};

/**
 * 状态机错误码 (STATE_)
 */
export const STATE_ERROR_CODES: Record<string, ErrorCodeInfo> = {
  STATE_400: {
    code: 'STATE_400',
    message: '非法状态流转',
    userMessage: '当前状态不允许此操作',
    action: '请检查当前状态',
  },
  STATE_401: {
    code: 'STATE_401',
    message: '跳过必要步骤',
    userMessage: '请按流程依次操作',
    action: '请先完成前置步骤',
  },
  STATE_402: {
    code: 'STATE_402',
    message: '终态非法回退',
    userMessage: '已完成的状态无法回退',
    action: '如需修改请联系管理员',
  },
  STATE_403: {
    code: 'STATE_403',
    message: '系统无权限流转',
    userMessage: '系统无法自动执行此操作',
    action: '请手动操作',
  },
  STATE_405: {
    code: 'STATE_405',
    message: '绝对禁止的流转',
    userMessage: '此操作被禁止',
    action: '如有疑问请联系管理员',
  },
  STATE_409: {
    code: 'STATE_409',
    message: '并发冲突',
    userMessage: '数据已被其他用户修改',
    action: '请刷新页面后重试',
  },
};

/**
 * 趋势风控错误码 (TREND_)
 */
export const TREND_ERROR_CODES: Record<string, ErrorCodeInfo> = {
  TREND_001: {
    code: 'TREND_001',
    message: '趋势风控触发',
    userMessage: '检测到数据异常波动',
    action: '请复核数据后继续',
  },
  TREND_002: {
    code: 'TREND_002',
    message: '风控复核未完成',
    userMessage: '请先完成风控复核',
    action: '请处理异常标记后继续',
  },
  TREND_010: {
    code: 'TREND_010',
    message: '复核原因缺失',
    userMessage: '请填写复核原因',
    action: '请说明异常处理原因',
  },
};

/**
 * 利润统计错误码 (PROFIT_)
 */
export const PROFIT_ERROR_CODES: Record<string, ErrorCodeInfo> = {
  PROFIT_001: {
    code: 'PROFIT_001',
    message: '指定期间无数据',
    userMessage: '该时间段暂无数据',
    action: '请选择其他时间段',
  },
  PROFIT_002: {
    code: 'PROFIT_002',
    message: '周期参数无效',
    userMessage: '时间参数不正确',
    action: '请检查日期范围',
  },
  PROFIT_005: {
    code: 'PROFIT_005',
    message: '无权限访问',
    userMessage: '您没有权限查看此数据',
    action: '请联系管理员',
  },
  PROFIT_008: {
    code: 'PROFIT_008',
    message: '数据已锁定',
    userMessage: '数据已锁定，无法修改',
    action: '如需修改请联系管理员',
  },
};

/**
 * 对账错误码 (REC_)
 */
export const REC_ERROR_CODES: Record<string, ErrorCodeInfo> = {
  REC_001: {
    code: 'REC_001',
    message: '对账守恒校验失败',
    userMessage: '对账数据存在差异',
    action: '请检查对账数据',
  },
  REC_002: {
    code: 'REC_002',
    message: '快照数据缺失',
    userMessage: '缺少必要的对账快照',
    action: '请联系管理员',
  },
  REC_004: {
    code: 'REC_004',
    message: '差异单操作权限不足',
    userMessage: '您不是该差异单的责任人',
    action: '只有责任人可以处理此差异单',
  },
};

/**
 * 结算错误码 (SET_)
 */
export const SET_ERROR_CODES: Record<string, ErrorCodeInfo> = {
  SET_001: {
    code: 'SET_001',
    message: '结算规则配置无效',
    userMessage: '结算规则配置有误',
    action: '请检查结算规则设置',
  },
  SET_002: {
    code: 'SET_002',
    message: '结算类型不支持',
    userMessage: '不支持的结算类型',
    action: '请选择有效的结算类型',
  },
  SET_003: {
    code: 'SET_003',
    message: '结算规则生效期冲突',
    userMessage: '结算规则生效期存在冲突',
    action: '请调整生效期避免重叠',
  },
};

// ============================================================================
// Error Code Map (All Codes)
// ============================================================================

/**
 * 所有错误码映射表
 */
export const ERROR_CODE_MAP: Record<string, ErrorCodeInfo> = {
  ...AUTH_ERROR_CODES,
  ...BIZ_ERROR_CODES,
  ...VALIDATION_ERROR_CODES,
  ...SYS_ERROR_CODES,
  ...DB_ERROR_CODES,
  ...STATE_ERROR_CODES,
  ...TREND_ERROR_CODES,
  ...PROFIT_ERROR_CODES,
  ...REC_ERROR_CODES,
  ...SET_ERROR_CODES,
};

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * 根据错误码获取错误信息
 * @param code 错误码
 * @returns 错误信息对象，如果找不到则返回默认错误信息
 */
export function getErrorInfo(code: string): ErrorCodeInfo {
  return (
    ERROR_CODE_MAP[code] || {
      code,
      message: '未知错误',
      userMessage: '操作失败',
      action: '请稍后重试',
    }
  );
}

/**
 * 获取用户友好的错误消息
 * @param code 错误码
 * @param fallbackMessage 后备消息（如果错误码未定义时使用）
 * @returns 用户友好的错误消息
 */
export function getUserMessage(code: string, fallbackMessage?: string): string {
  const info = ERROR_CODE_MAP[code];
  if (info) {
    return info.userMessage;
  }
  return fallbackMessage || '操作失败，请稍后重试';
}

/**
 * 获取错误建议操作
 * @param code 错误码
 * @returns 建议用户采取的操作
 */
export function getErrorAction(code: string): string | undefined {
  return ERROR_CODE_MAP[code]?.action;
}

/**
 * 判断是否为认证相关错误
 * @param code 错误码
 */
export function isAuthError(code: string): boolean {
  return code.startsWith('AUTH_');
}

/**
 * 判断是否为需要重新登录的错误
 * @param code 错误码
 */
export function isSessionExpiredError(code: string): boolean {
  return ['AUTH_400', 'AUTH_401', 'AUTH_402', 'AUTH_003'].includes(code);
}

/**
 * 判断是否为权限不足错误
 * @param code 错误码
 */
export function isPermissionError(code: string): boolean {
  return ['AUTH_500', 'AUTH_501', 'PROFIT_005', 'REC_004'].includes(code);
}

/**
 * 判断是否为数据冲突错误（需要刷新）
 * @param code 错误码
 */
export function isConflictError(code: string): boolean {
  return ['STATE_409', 'BIZ_003', 'DB_004'].includes(code);
}

/**
 * 判断是否为验证错误
 * @param code 错误码
 */
export function isValidationError(code: string): boolean {
  return code.startsWith('VALIDATION_');
}

/**
 * 格式化完整的错误消息（包含建议操作）
 * @param code 错误码
 * @param originalMessage 原始错误消息
 * @returns 完整的错误消息
 */
export function formatErrorMessage(code: string, originalMessage?: string): string {
  const info = ERROR_CODE_MAP[code];
  if (!info) {
    return originalMessage || '操作失败，请稍后重试';
  }

  let message = info.userMessage;
  if (info.action) {
    message += `。${info.action}`;
  }
  return message;
}
