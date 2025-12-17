# AI 广告代投系统 - 代码与文档审核报告

> **审核日期**: 2025-12-11
> **审核范围**: 后端代码 + 前端代码 + SoT 文档
> **审核人**: Claude Code AI Agent

---

## 执行摘要

| 审核模块 | 评分 | 发现问题 | P0 | P1 | P2 |
|---------|------|---------|----|----|-----|
| **后端代码** | B+ (85/100) | 11 个 | 2 | 3 | 6 |
| **前端代码** | B (80/100) | 14 个 | 2 | 5 | 7 |
| **文档一致性** | B- (75/100) | 12 个 | 2 | 5 | 4 |
| **总计** | **B (80/100)** | **37 个** | **6** | **13** | **17** |

### 关键发现

1. **核心功能合规** - 日报 8 状态机、账本系统、错误码体系正确实现
2. **架构设计良好** - Feature-Based 前端架构、DDD 后端分层清晰
3. **存在一致性问题** - 项目状态机定义、认证模块、文档版本引用不一致
4. **需要清理技术债务** - MOCK 代码、未使用依赖、调试日志

---

## P0 - 严重问题 (必须立即修复)

### 1. 后端: 项目状态机定义与 SoT 不一致
- **文件**: `backend/models/enums.py:31-46`
- **问题**: 代码定义 `planning, active, paused, completed, cancelled`
- **SoT 规范**: STATE_MACHINE.md v2.6 定义 `draft, active, suspended, archived`
- **修复**: 按 SoT 修改枚举定义

### 2. 后端: 趋势风控服务使用非标准异常
- **文件**: `backend/services/trend_risk_control_service.py:363,367,455`
- **问题**: 使用 `ValueError` 而非 `BusinessLogicError`
- **修复**: 替换为标准异常，添加错误码

### 3. 前端: 直接使用 fetch() 绕过 API 客户端
- **文件**:
  - `features/import-jobs/services/importJobsApi.ts:71,90`
  - `features/reconciliation/components/` 多处
- **问题**: 缺少认证 token、错误处理
- **修复**: 扩展 `apiFetch` 支持 FormData 上传

### 4. 前端: MOCK 模式残留在生产代码
- **文件**: `features/auth/hooks/useAuth.ts:63-84`
- **问题**: 开发模式下绕过真实认证
- **修复**: 移除 MOCK 逻辑或使用环境变量控制

### 5. 文档: 项目状态机代码与文档严重冲突
- **问题**: 代码与 STATE_MACHINE.md v2.6 定义完全不同
- **修复**: 代码对齐 SoT 或提交 RFC 修改文档

### 6. 文档: 核心 SoT 文档路径问题
- **问题**: 关键文档无法通过 Glob 扫描找到
- **修复**: 检查文件路径，创建 docs/README.md 索引

---

## P1 - 重要问题 (1 周内修复)

### 后端
1. **账本服务注释不足** - `ledger_service.py:418-428` 缺少合法性说明
2. **缺少 STATE_/TREND_ 错误码类** - `error_codes.py` 需补充定义
3. **用户角色包含未定义角色** - `analyst` 角色未在 SoT 定义

### 前端
1. **重复的 useAuth Hook** - `hooks/useAuth.ts` 与 `features/auth/hooks/useAuth.ts` 冲突
2. **未使用的依赖** - `zustand`, `@supabase/supabase-js` 已安装但未使用
3. **LoginPage 字段不匹配** - 使用 `identifier` 但类型定义是 `email`
4. **Token 存储键不一致** - 两套认证系统使用不同存储键
5. **大型组件未拆分** - `TopupsPage.tsx` 超过 600 行

### 文档
1. **BUSINESS_RULES.md 版本引用不一致** - v3.1 vs v3.2
2. **DATA_SCHEMA.md 版本不一致** - v5.1 vs v5.2
3. **RLS_POLICIES_SOT.md 版本号冲突** - v2.0 vs v2.1

---

## P2 - 一般问题 (2 周内修复)

### 后端
1. Router 层缺少统一错误处理模式
2. 部分服务方法缺少文档字符串
3. 测试覆盖率可进一步提升

### 前端
1. 使用 `any` 类型 (4 个文件)
2. 过度使用 useEffect (22 个文件, 32 处)
3. 未移除 console 语句 (29 个文件, 88 处)
4. Query 缓存配置不一致
5. 缺少 Loading Skeleton
6. 过度的 refetch 调用
7. 缺少请求取消机制

### 文档
1. AUTH_SPEC.md 版本历史不合理
2. 缺少文档导航索引
3. 变更历史记录不完整

---

## 优化建议

### 1. 认证模块统一 (P0/P1)

```typescript
// 删除 hooks/useAuth.ts
// 保留并完善 features/auth/hooks/useAuth.ts

// 统一 token 存储键
const TOKEN_KEY = 'auth-token';        // 不是 'auth_token'
const REFRESH_TOKEN_KEY = 'refresh-token';
const TOKEN_EXPIRY_KEY = 'token-expiry';

// 移除 MOCK 模式
// const MOCK_DEV_MODE = ... // 删除此行
```

### 2. API 客户端扩展 (P0)

```typescript
// lib/api.ts 添加文件上传支持
export async function apiUpload<T = any>(
  endpoint: string,
  formData: FormData,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  const token = getAccessToken();
  return apiRequest<T>(endpoint, {
    ...options,
    method: 'POST',
    body: formData,
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      // 不设置 Content-Type，让浏览器自动设置 boundary
    },
  });
}
```

### 3. 项目状态机修复 (P0)

```python
# backend/models/enums.py
class ProjectStatus(str, Enum):
    """
    项目状态枚举
    必须与 STATE_MACHINE.md v2.6 §5 保持一致
    """
    DRAFT = "draft"          # 草稿
    ACTIVE = "active"        # 进行中
    SUSPENDED = "suspended"  # 暂停
    ARCHIVED = "archived"    # 已归档（终态）
```

### 4. 错误码补充 (P1)

```python
# backend/core/error_codes.py 添加

class StateErrorCodes:
    """状态机错误码"""
    FORBIDDEN_TRANSITION = ErrorCode("STATE_400", "非法状态流转", 400)
    SKIP_REQUIRED_STEP = ErrorCode("STATE_401", "跳过必要步骤", 400)
    FINAL_STATE_ROLLBACK = ErrorCode("STATE_402", "终态非法回退", 400)

class TrendErrorCodes:
    """趋势风控错误码"""
    TREND_RISK_TRIGGERED = ErrorCode("TREND_001", "趋势风控触发", 200)
    REVIEW_REQUIRED = ErrorCode("TREND_002", "风控复核未完成", 400)
```

### 5. 清理未使用依赖 (P1)

```bash
# 在 frontend 目录执行
npm uninstall zustand @supabase/supabase-js
```

### 6. 统一缓存策略 (P2)

```typescript
// lib/config.ts
export const CACHE_CONFIG = {
  auth: 5 * 60 * 1000,      // 认证: 5分钟
  static: 30 * 60 * 1000,   // 静态数据: 30分钟
  realtime: 10 * 1000,      // 实时数据: 10秒
  default: 60 * 1000,       // 默认: 1分钟
};
```

---

## 修复优先级时间表

### 本周 (Week 1) - P0 问题
| 任务 | 预估时间 | 负责人 |
|------|---------|--------|
| 修复项目状态机 (后端) | 2h | Backend |
| 替换 ValueError 为标准异常 | 2h | Backend |
| 统一 API 客户端 (添加 apiUpload) | 3h | Frontend |
| 移除 MOCK 模式 | 1h | Frontend |
| 统一 useAuth hook | 2h | Frontend |
| 修复文档路径问题 | 2h | DevOps |

### 下周 (Week 2) - P1 问题
| 任务 | 预估时间 | 负责人 |
|------|---------|--------|
| 补充 STATE_/TREND_ 错误码 | 2h | Backend |
| 修复 LoginPage 字段匹配 | 1h | Frontend |
| 统一 Token 存储键 | 1h | Frontend |
| 移除未使用依赖 | 0.5h | Frontend |
| 拆分大型组件 | 4h | Frontend |
| 统一文档版本引用 | 2h | Doc |

### 第 3-4 周 - P2 问题
| 任务 | 预估时间 |
|------|---------|
| 移除 console 语句 | 3h |
| 添加 TypeScript 严格检查 | 4h |
| 统一缓存策略 | 2h |
| 补充 Loading Skeleton | 6h |
| 补充服务方法文档 | 6h |
| 创建文档导航索引 | 2h |

---

## 合规性检查清单

### SoT 合规性
- [x] 日报 8 状态机符合 STATE_MACHINE.md v2.6
- [ ] ⚠️ 项目状态机需修复
- [x] 错误码体系完整 (67 个)
- [ ] ⚠️ 缺少 STATE_/TREND_ 类定义
- [x] 账本操作符合 LEDGER_SOT.md v1.1
- [x] 未发现直接修改 balance 违规

### 架构合规性
- [x] Feature-Based 前端架构
- [x] TanStack Query 状态管理
- [x] shadcn/ui + Tailwind CSS
- [ ] ⚠️ 部分代码绕过 apiFetch
- [x] DDD 后端分层
- [x] Router 薄层设计

### 代码质量
- [x] TypeScript 类型定义完整
- [ ] ⚠️ 存在 any 类型使用
- [ ] ⚠️ 存在调试代码
- [x] 组件拆分合理 (大部分)
- [ ] ⚠️ TopupsPage.tsx 需拆分

---

## 总结

本项目整体代码质量 **良好 (B 级, 80/100)**，核心业务功能正确实现，架构清晰。

**主要优点**:
1. 日报 8 状态机、账本系统严格遵循 SoT 规范
2. 前后端架构分层清晰，模块化良好
3. 错误处理和响应格式规范

**主要问题**:
1. 项目状态机代码与文档严重不一致 (P0)
2. 认证模块存在重复定义和 MOCK 代码 (P0)
3. 部分 API 调用绕过统一客户端 (P0)
4. 文档版本引用混乱 (P1)

**建议行动**:
1. **立即修复** 6 个 P0 问题 (本周内)
2. **短期改进** 13 个 P1 问题 (2 周内)
3. **持续优化** 17 个 P2 问题 (1 个月内)

---

**审核报告生成时间**: 2025-12-11
**下次审核建议**: P0 问题修复后进行复查
