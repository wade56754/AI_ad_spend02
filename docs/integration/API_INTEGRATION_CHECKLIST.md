# API对接清单

> **文档版本**: v1.0
> **最后更新**: 2025-12-10
> **文档类型**: 开发清单
> **适用范围**: 前端开发人员

---

## 目录

1. [清单说明](#1-清单说明)
2. [认证模块](#2-认证模块-api-v1-auth)
3. [项目管理](#3-项目管理-api-v1-projects)
4. [日报管理](#4-日报管理-api-v1-daily-reports)
5. [充值管理](#5-充值管理-api-v1-topups)
6. [供应商管理](#6-供应商管理-api-v1-suppliers)
7. [结算管理](#7-结算管理-api-v1-settlements)
8. [对账管理](#8-对账管理-api-v1-reconciliation)
9. [报表中心](#9-报表中心-api-v1-reports)
10. [其他模块](#10-其他模块)

---

## 1. 清单说明

### 1.1 优先级定义

- **P0**: 核心功能，必须实现
- **P1**: 重要功能，尽快实现
- **P2**: 常规功能，按计划实现
- **P3**: 可选功能，有时间再实现

### 1.2 状态标识

- ✅ **已实现**: 后端API已实现，前端可以调用
- 🟡 **部分实现**: 后端有API但前端未集成
- ❌ **未实现**: 需要开发
- 🔧 **待修复**: 有bug需要修复

### 1.3 使用说明

每个API端点包含：
- **端点**: 完整的API路径
- **方法**: HTTP方法
- **权限**: 需要的角色权限
- **状态**: 实现状态
- **优先级**: 开发优先级
- **前端页面**: 需要调用此API的页面
- **依赖**: 依赖的其他API或数据

---

## 2. 认证模块 (/api/v1/auth)

### 2.1 用户注册与登录

| 端点 | 方法 | 功能 | 权限 | 状态 | 优先级 | 前端页面 |
|------|------|------|------|------|--------|----------|
| `/auth/register` | POST | 用户注册 | 公开 | ✅ | P0 | /register |
| `/auth/login` | POST | 用户登录 | 公开 | ✅ | P0 | /login |
| `/auth/logout` | POST | 用户登出 | 需认证 | ✅ | P0 | 全局 |
| `/auth/logout-all` | POST | 登出所有设备 | 需认证 | ✅ | P2 | /settings |

**实现要点**:
- 登录成功后保存Token到localStorage
- 实现自动登出（Token过期）
- 登出后清除本地存储
- 错误提示用户友好

### 2.2 Token管理

| 端点 | 方法 | 功能 | 权限 | 状态 | 优先级 | 前端页面 |
|------|------|------|------|------|--------|----------|
| `/auth/refresh` | POST | 刷新Token | 公开 | ✅ | P0 | 全局拦截器 |
| `/auth/verify-token` | POST | 验证Token | 需认证 | ✅ | P1 | 全局拦截器 |

**实现要点**:
- 在API拦截器中自动刷新Token
- Token过期前5分钟自动刷新
- 刷新失败跳转登录页

### 2.3 用户信息

| 端点 | 方法 | 功能 | 权限 | 状态 | 优先级 | 前端页面 |
|------|------|------|------|------|--------|----------|
| `/auth/me` | GET | 获取当前用户 | 需认证 | ✅ | P0 | 全局布局 |
| `/auth/change-password` | POST | 修改密码 | 需认证 | ✅ | P1 | /settings |
| `/auth/forgot-password` | POST | 忘记密码 | 公开 | ✅ | P2 | /forgot-password |
| `/auth/reset-password` | POST | 重置密码 | 公开 | ✅ | P2 | /reset-password |

**实现要点**:
- 在布局组件中获取用户信息
- 修改密码后强制重新登录
- 密码强度验证

---

## 3. 项目管理 (/api/v1/projects)

### 3.1 项目CRUD

| 端点 | 方法 | 功能 | 权限 | 状态 | 优先级 | 前端页面 |
|------|------|------|------|------|--------|----------|
| `/projects` | GET | 获取项目列表 | 需认证 | ✅ | P0 | /projects |
| `/projects/{id}` | GET | 获取项目详情 | 需认证 | ✅ | P0 | /projects/[id] |
| `/projects` | POST | 创建项目 | admin/finance | ✅ | P0 | /projects |
| `/projects/{id}` | PUT | 更新项目 | admin/finance | ✅ | P0 | /projects/[id] |
| `/projects/{id}` | DELETE | 删除项目 | admin | ✅ | P1 | /projects |

**实现要点**:
- 列表支持分页、搜索、筛选
- 详情页展示完整信息
- 创建/编辑表单验证
- 删除前确认提示

**查询参数**:
```typescript
interface ProjectQueryParams {
  page?: number           // 页码
  page_size?: number      // 每页数量
  status?: string         // 状态筛选
  search?: string         // 搜索关键词
  client_name?: string    // 客户名称
  date_from?: string      // 开始日期
  date_to?: string        // 结束日期
}
```

### 3.2 项目统计

| 端点 | 方法 | 功能 | 权限 | 状态 | 优先级 | 前端页面 |
|------|------|------|------|------|--------|----------|
| `/projects/statistics` | GET | 项目统计数据 | 需认证 | ✅ | P0 | /dashboard |
| `/projects/{id}/statistics` | GET | 单个项目统计 | 需认证 | ✅ | P1 | /projects/[id] |

**实现要点**:
- 仪表盘展示总体统计
- 项目详情页展示单项目统计
- 数据可视化（图表）

### 3.3 项目成员

| 端点 | 方法 | 功能 | 权限 | 状态 | 优先级 | 前端页面 |
|------|------|------|------|------|--------|----------|
| `/projects/{id}/members` | GET | 获取成员列表 | 需认证 | ✅ | P1 | /projects/[id]/members |
| `/projects/{id}/members` | POST | 添加成员 | admin/finance | ✅ | P1 | /projects/[id]/members |
| `/projects/{id}/members/{member_id}` | DELETE | 移除成员 | admin/finance | ✅ | P1 | /projects/[id]/members |

**实现要点**:
- 成员列表展示
- 添加成员模态框
- 移除成员确认

---

## 4. 日报管理 (/api/v1/daily-reports)

### 4.1 日报CRUD

| 端点 | 方法 | 功能 | 权限 | 状态 | 优先级 | 前端页面 |
|------|------|------|------|------|--------|----------|
| `/daily-reports` | GET | 获取日报列表 | 需认证 | ✅ | P0 | /daily-reports |
| `/daily-reports/{id}` | GET | 获取日报详情 | 需认证 | ✅ | P0 | /daily-reports/[id] |
| `/daily-reports` | POST | 创建日报 | media_buyer | ✅ | P0 | /daily-reports |
| `/daily-reports/{id}` | PUT | 更新日报 | media_buyer | ✅ | P0 | /daily-reports/[id] |
| `/daily-reports/{id}` | DELETE | 删除日报 | admin | ✅ | P2 | /daily-reports |

**实现要点**:
- 投手每日提交日报
- 支持批量导入（Excel）
- 数据验证（必填字段、格式）
- 状态流转展示

**请求参数**:
```typescript
interface DailyReportCreateRequest {
  project_id: number
  report_date: string         // YYYY-MM-DD
  ad_account_id: number
  conversions_raw: number     // raw数据流
  raw_spend: number           // raw花费
  real_spend?: number         // real花费（运营填写）
  conversions_final?: number  // final转化（运营确认）
  notes?: string
}
```

### 4.2 日报审核

| 端点 | 方法 | 功能 | 权限 | 状态 | 优先级 | 前端页面 |
|------|------|------|------|------|--------|----------|
| `/daily-reports/{id}/audit` | POST | 审核日报 | data_operator | ✅ | P0 | /daily-reports/[id] |
| `/daily-reports/{id}/audit-logs` | GET | 审核日志 | 需认证 | ✅ | P1 | /daily-reports/[id] |

**实现要点**:
- 运营审核界面
- 支持通过/驳回
- 驳回需填写原因
- 审核日志展示

**审核请求**:
```typescript
interface DailyReportAuditRequest {
  action: 'approve' | 'reject'
  notes?: string
  real_spend?: number         // 审核时确认real_spend
  conversions_final?: number  // 审核时确认final转化
}
```

### 4.3 日报统计与导出

| 端点 | 方法 | 功能 | 权限 | 状态 | 优先级 | 前端页面 |
|------|------|------|------|------|--------|----------|
| `/daily-reports/statistics` | GET | 日报统计 | 需认证 | ✅ | P0 | /dashboard |
| `/daily-reports/export` | POST | 导出Excel | 需认证 | ✅ | P1 | /daily-reports |
| `/daily-reports/import` | POST | 导入Excel | media_buyer | ✅ | P1 | /daily-reports |

**实现要点**:
- 统计卡片展示
- Excel导出下载
- Excel导入上传
- 导入错误提示

---

## 5. 充值管理 (/api/v1/topups)

### 5.1 充值申请CRUD

| 端点 | 方法 | 功能 | 权限 | 状态 | 优先级 | 前端页面 |
|------|------|------|------|------|--------|----------|
| `/topups` | GET | 获取充值列表 | 需认证 | ✅ | P0 | /topups |
| `/topups/{id}` | GET | 获取充值详情 | 需认证 | ✅ | P0 | /topups/[id] |
| `/topups` | POST | 创建充值申请 | media_buyer | ✅ | P0 | /topups |
| `/topups/{id}` | PUT | 更新充值申请 | media_buyer | ✅ | P1 | /topups/[id] |
| `/topups/{id}` | DELETE | 取消充值申请 | media_buyer | ✅ | P1 | /topups |

**实现要点**:
- 投手创建充值申请
- 查看充值进度
- 可以取消未审核的申请

**创建请求**:
```typescript
interface TopupRequestCreate {
  ad_account_id: number
  amount: number          // 充值金额
  urgency_level?: string  // 紧急程度: normal/urgent/critical
  reason?: string         // 充值原因
  expected_date?: string  // 期望充值日期
}
```

### 5.2 充值审核流程

| 端点 | 方法 | 功能 | 权限 | 状态 | 优先级 | 前端页面 |
|------|------|------|------|------|--------|----------|
| `/topups/{id}/data-review` | POST | 数据审核 | data_operator | ✅ | P0 | /topups/[id] |
| `/topups/{id}/finance-approval` | POST | 财务审批 | finance | ✅ | P0 | /topups/[id] |
| `/topups/{id}/mark-paid` | POST | 标记已打款 | finance | ✅ | P0 | /topups/[id] |
| `/topups/{id}/receipt` | POST | 上传凭证 | finance | ✅ | P1 | /topups/[id] |

**实现要点**:
- 数据员审核界面
- 财务审批界面
- 打款标记
- 凭证上传

**审核流程**:
```
pending → data_reviewed → finance_approved → paid → completed
   ↓
rejected (任何阶段)
```

### 5.3 充值统计

| 端点 | 方法 | 功能 | 权限 | 状态 | 优先级 | 前端页面 |
|------|------|------|------|------|--------|----------|
| `/topups/statistics` | GET | 充值统计 | 需认证 | ✅ | P0 | /dashboard |
| `/topups/dashboard` | GET | 充值仪表盘 | finance | ✅ | P1 | /topups |

**实现要点**:
- 总充值金额
- 待审核数量
- 已完成数量
- 趋势图表

---

## 6. 供应商管理 (/api/v1/suppliers)

### 6.1 供应商CRUD

| 端点 | 方法 | 功能 | 权限 | 状态 | 优先级 | 前端页面 |
|------|------|------|------|------|--------|----------|
| `/suppliers` | GET | 获取供应商列表 | 需认证 | ✅ | P0 | /suppliers |
| `/suppliers/{id}` | GET | 获取供应商详情 | 需认证 | ✅ | P0 | /suppliers/[id] |
| `/suppliers` | POST | 创建供应商 | admin/finance | ✅ | P0 | /suppliers |
| `/suppliers/{id}` | PUT | 更新供应商 | admin/finance | ✅ | P0 | /suppliers/[id] |
| `/suppliers/{id}` | DELETE | 删除供应商 | admin | ✅ | P2 | /suppliers |

**实现要点**:
- 供应商列表
- 详情页展示账户信息
- 创建/编辑表单

**创建请求**:
```typescript
interface SupplierCreate {
  name: string
  contact_name?: string
  contact_phone?: string
  contact_email?: string
  payment_terms?: string
  notes?: string
}
```

### 6.2 供应商账户

| 端点 | 方法 | 功能 | 权限 | 状态 | 优先级 | 前端页面 |
|------|------|------|------|------|--------|----------|
| `/suppliers/{id}/accounts` | GET | 获取账户列表 | 需认证 | ✅ | P0 | /suppliers/[id] |
| `/suppliers/{id}/ledger-summary` | GET | 账本汇总 | finance | ✅ | P1 | /suppliers/[id] |

**实现要点**:
- 账户列表展示
- 余额信息
- 账本明细

### 6.3 供应商统计

| 端点 | 方法 | 功能 | 权限 | 状态 | 优先级 | 前端页面 |
|------|------|------|------|------|--------|----------|
| `/suppliers/statistics` | GET | 供应商统计 | finance | ✅ | P1 | /suppliers |

**实现要点**:
- 总供应商数
- 活跃账户数
- 总余额

---

## 7. 结算管理 (/api/v1/settlements)

### 7.1 结算CRUD

| 端点 | 方法 | 功能 | 权限 | 状态 | 优先级 | 前端页面 |
|------|------|------|------|------|--------|----------|
| `/settlements` | GET | 获取结算列表 | 需认证 | ✅ | P0 | /settlements |
| `/settlements/{id}` | GET | 获取结算详情 | 需认证 | ✅ | P0 | /settlements/[id] |
| `/settlements` | POST | 创建结算 | finance | ✅ | P0 | /settlements |
| `/settlements/{id}` | PUT | 更新结算 | finance | ✅ | P1 | /settlements/[id] |

**实现要点**:
- 结算列表
- 结算详情
- 创建结算单

**创建请求**:
```typescript
interface SettlementCreate {
  supplier_id: number
  settlement_date: string
  amount: number
  payment_method?: string
  notes?: string
}
```

### 7.2 结算审核

| 端点 | 方法 | 功能 | 权限 | 状态 | 优先级 | 前端页面 |
|------|------|------|------|------|--------|----------|
| `/settlements/{id}/approve` | POST | 审批结算 | admin | ✅ | P0 | /settlements/[id] |
| `/settlements/{id}/reject` | POST | 拒绝结算 | admin | ✅ | P0 | /settlements/[id] |
| `/settlements/{id}/mark-paid` | POST | 标记已支付 | finance | ✅ | P0 | /settlements/[id] |

**实现要点**:
- 审批流程
- 拒绝原因
- 支付标记

### 7.3 结算统计

| 端点 | 方法 | 功能 | 权限 | 状态 | 优先级 | 前端页面 |
|------|------|------|------|------|--------|----------|
| `/settlements/statistics` | GET | 结算统计 | finance | ✅ | P0 | /settlements |
| `/settlements/overdue` | GET | 逾期结算 | finance | ✅ | P1 | /settlements |

**实现要点**:
- 待结算金额
- 已结算金额
- 逾期提醒

---

## 8. 对账管理 (/api/v1/reconciliation)

### 8.1 对账CRUD

| 端点 | 方法 | 功能 | 权限 | 状态 | 优先级 | 前端页面 |
|------|------|------|------|------|--------|----------|
| `/reconciliation` | GET | 获取对账列表 | 需认证 | ✅ | P0 | /reconciliation |
| `/reconciliation/{id}` | GET | 获取对账详情 | 需认证 | ✅ | P0 | /reconciliation/[id] |
| `/reconciliation` | POST | 创建对账 | data_operator | ✅ | P0 | /reconciliation |
| `/reconciliation/{id}` | PUT | 更新对账 | data_operator | ✅ | P1 | /reconciliation/[id] |

**实现要点**:
- 对账列表
- 差异展示
- 创建对账单

**创建请求**:
```typescript
interface ReconciliationCreate {
  project_id: number
  reconciliation_date: string
  period_start: string
  period_end: string
}
```

### 8.2 差异处理

| 端点 | 方法 | 功能 | 权限 | 状态 | 优先级 | 前端页面 |
|------|------|------|------|------|--------|----------|
| `/reconciliation/{id}/mismatches` | GET | 获取差异列表 | 需认证 | ✅ | P0 | /reconciliation/[id] |
| `/reconciliation/{id}/resolve` | POST | 解决差异 | data_operator | ✅ | P1 | /reconciliation/[id] |

**实现要点**:
- 差异列表
- 差异原因
- 解决方案

---

## 9. 报表中心 (/api/v1/reports)

### 9.1 仪表盘

| 端点 | 方法 | 功能 | 权限 | 状态 | 优先级 | 前端页面 |
|------|------|------|------|------|--------|----------|
| `/reports/dashboard` | GET | 仪表盘数据 | 需认证 | ✅ | P0 | /dashboard |

**实现要点**:
- 关键指标卡片
- 趋势图表
- 近期活动

### 9.2 专项报表

| 端点 | 方法 | 功能 | 权限 | 状态 | 优先级 | 前端页面 |
|------|------|------|------|------|--------|----------|
| `/reports/performance` | GET | 绩效报表 | admin/finance | ✅ | P1 | /reports/performance |
| `/reports/profit` | GET | 利润报表 | admin/finance | ✅ | P1 | /reports/profit |
| `/reports/financial` | GET | 财务报表 | finance | ✅ | P1 | /reports/financial |
| `/reports/reconciliation` | GET | 对账报表 | finance | ✅ | P1 | /reports/reconciliation |

**实现要点**:
- 多维度报表
- 图表可视化
- 数据导出

### 9.3 趋势分析

| 端点 | 方法 | 功能 | 权限 | 状态 | 优先级 | 前端页面 |
|------|------|------|------|------|--------|----------|
| `/reports/trends/{metric}` | GET | 趋势分析 | 需认证 | ✅ | P1 | /reports/trends |

**实现要点**:
- 时间序列图表
- 指标选择
- 时间范围筛选

---

## 10. 其他模块

### 10.1 广告账户 (/api/v1/ad-accounts)

| 端点 | 方法 | 功能 | 权限 | 状态 | 优先级 |
|------|------|------|------|------|--------|
| `/ad-accounts` | GET | 获取账户列表 | 需认证 | ✅ | P1 |
| `/ad-accounts/{id}` | GET | 获取账户详情 | 需认证 | ✅ | P1 |
| `/ad-accounts` | POST | 创建账户 | admin/account_manager | ✅ | P1 |
| `/ad-accounts/{id}` | PUT | 更新账户 | admin/account_manager | ✅ | P1 |
| `/ad-accounts/{id}` | DELETE | 删除账户 | admin | ✅ | P2 |

### 10.2 渠道管理 (/api/v1/channels)

| 端点 | 方法 | 功能 | 权限 | 状态 | 优先级 |
|------|------|------|------|------|--------|
| `/channels` | GET | 获取渠道列表 | 需认证 | ✅ | P2 |
| `/channels/{id}` | GET | 获取渠道详情 | 需认证 | ✅ | P2 |

### 10.3 财务总账 (/api/v1/ledger)

| 端点 | 方法 | 功能 | 权限 | 状态 | 优先级 |
|------|------|------|------|------|--------|
| `/ledger` | GET | 获取账本列表 | finance | ✅ | P1 |
| `/ledger/{id}` | GET | 获取账本详情 | finance | ✅ | P1 |

### 10.4 余额转移 (/api/v1/transfers)

| 端点 | 方法 | 功能 | 权限 | 状态 | 优先级 |
|------|------|------|------|------|--------|
| `/transfers` | GET | 获取转移列表 | 需认证 | ✅ | P2 |
| `/transfers` | POST | 创建转移 | data_operator | ✅ | P2 |

### 10.5 数据导入 (/api/v1/import-jobs)

| 端点 | 方法 | 功能 | 权限 | 状态 | 优先级 |
|------|------|------|------|------|--------|
| `/import-jobs` | GET | 获取导入任务 | 需认证 | ✅ | P2 |
| `/import-jobs` | POST | 创建导入任务 | data_operator | ✅ | P2 |
| `/import-jobs/{id}` | GET | 获取任务详情 | 需认证 | ✅ | P2 |

---

## 附录A: 开发优先级建议

### 第一阶段 (Week 1-2): P0核心功能

1. **认证模块** (2天)
   - 登录/登出
   - Token管理
   - 用户信息获取

2. **项目管理** (2天)
   - 项目列表/详情
   - 项目CRUD
   - 项目统计

3. **日报管理** (3天)
   - 日报列表/详情
   - 日报创建/编辑
   - 日报审核流程
   - 日报统计

4. **充值管理** (2天)
   - 充值列表/详情
   - 充值申请
   - 充值审核流程

5. **仪表盘** (2天)
   - 关键指标展示
   - 趋势图表
   - 快速入口

### 第二阶段 (Week 3-4): P1重要功能

1. **供应商管理** (2天)
   - 供应商CRUD
   - 供应商账户
   - 供应商统计

2. **结算管理** (2天)
   - 结算列表/详情
   - 结算创建
   - 结算审核

3. **对账管理** (2天)
   - 对账列表
   - 差异展示
   - 差异处理

4. **报表中心** (2天)
   - 绩效报表
   - 利润报表
   - 财务报表

5. **其他功能** (2天)
   - 广告账户
   - 财务总账
   - 批量操作

### 第三阶段 (Week 5-6): P2常规功能

1. **功能完善** (3天)
   - 数据导入导出
   - 批量操作优化
   - 搜索筛选增强

2. **用户体验** (3天)
   - Loading状态
   - 错误提示优化
   - 表单验证优化

3. **性能优化** (2天)
   - 列表分页优化
   - 缓存策略
   - 请求优化

4. **测试与文档** (2天)
   - 单元测试
   - 集成测试
   - 文档完善

---

## 附录B: 前端技术建议

### React Query使用

```typescript
// hooks/useProjects.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiGet, apiPost, apiPut, apiDelete, queryKeys } from '@/lib/api'

// 查询项目列表
export function useProjects(params?: Record<string, unknown>) {
  return useQuery({
    queryKey: queryKeys.projects.list(params),
    queryFn: () => apiGet('/api/v1/projects', params),
  })
}

// 查询项目详情
export function useProject(id: number) {
  return useQuery({
    queryKey: queryKeys.projects.detail(id),
    queryFn: () => apiGet(`/api/v1/projects/${id}`),
    enabled: !!id,
  })
}

// 创建项目
export function useCreateProject() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: any) => apiPost('/api/v1/projects', data),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.projects.lists()
      })
    }
  })
}

// 更新项目
export function useUpdateProject() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) =>
      apiPut(`/api/v1/projects/${id}`, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.projects.detail(id)
      })
      queryClient.invalidateQueries({
        queryKey: queryKeys.projects.lists()
      })
    }
  })
}

// 删除项目
export function useDeleteProject() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => apiDelete(`/api/v1/projects/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.projects.lists()
      })
    }
  })
}
```

### 组件使用示例

```typescript
// pages/projects/index.tsx
import { useProjects, useDeleteProject } from '@/hooks/useProjects'

export default function ProjectsPage() {
  const { data, isLoading, error } = useProjects({ page: 1, page_size: 20 })
  const deleteProject = useDeleteProject()

  const handleDelete = async (id: number) => {
    if (confirm('确定要删除吗?')) {
      await deleteProject.mutateAsync(id)
    }
  }

  if (isLoading) return <div>加载中...</div>
  if (error) return <div>错误: {error.message}</div>

  return (
    <div>
      {data?.data?.map(project => (
        <div key={project.id}>
          <h3>{project.name}</h3>
          <button onClick={() => handleDelete(project.id)}>删除</button>
        </div>
      ))}
    </div>
  )
}
```

---

**文档维护者**: AI Development Team
**相关文档**:
- [FRONTEND_BACKEND_INTEGRATION.md](./FRONTEND_BACKEND_INTEGRATION.md) - 集成方案
- [QUICK_START.md](./QUICK_START.md) - 快速启动
- [API_SOT.md](../2.sot/API_SOT.md) - API规范
