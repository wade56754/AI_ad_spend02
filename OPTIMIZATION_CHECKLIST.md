# AI_ad_spend02 优化清单

> 目标：统一前后端接口契约、提升稳定性与一致性、完善工程化与可运维性。

- 优先级说明
  - P0：立即修复，影响正确性/用户体验
  - P1：重要改进，提升稳定性与一致性
  - P2：工程化/质量完善

## P0 立即项

- [ ] 统一 API 响应包裹结构与异常处理
  - 痛点：当前抛 `HTTPException` 导致返回 `{"detail":...}`，而前端与测试要求 `{"data":...,"error":...,"meta":...}`（lib/api.ts 强校验；tests 断言 `error`）。
  - 变更
    - 新增 `backend/core/response.py`：定义 `ApiResponse[T]`、`ok(data)`、`fail(error)`。
    - 在 `backend/main.py` 注册全局异常处理：
      - `HTTPException` → 包成 `{"data":null,"error":detail,"meta":...}`，HTTP 状态码保持。
      - 其他异常 → 500 同一结构（开发可回显 `debug` 下的错误信息）。
    - 路由统一 `return ok(data)`；可保留 `HTTPException` 但会被 handler 转换。
  - 验收
    - 前端 `apiFetch` 不再报“响应结构无效/解析失败”。
    - 测试 `backend/tests/*` 全部通过；重复写入返回 409 且 `error` 字段正确。

- [ ] 规范 API Base URL（避免 `/api/api`）
  - 痛点：文档示例用 `NEXT_PUBLIC_API_URL=http://localhost:8000/api`，而 `lib/api.ts` 会再拼 `/api/*`，导致 404。
  - 变更（二选一）
    - A：文档改为 `NEXT_PUBLIC_API_URL=http://localhost:8000`。
    - B：`lib/api.ts` 在拼接前去除末尾的 `/api` 与斜杠。
  - 验收
    - `app/finance/topups`、`app/reports/daily`、`app/projects` 的 API 请求正常返回。

- [ ] Topup 关联一致性校验
  - 痛点：`POST /api/topups` 未校验 `ad_account_id` 与 `project_id/channel_id` 是否一致，存在脏数据风险。
  - 变更
    - 在 `backend/routers/topups.py` 的 `create_topup` 中：查询 `AdAccount` 并校验 `project_id/channel_id` 与请求一致，不一致 422。
  - 验收
    - 传入不一致组合返回 422，错误信息明确；一致组合正常创建。

- [ ] 金额/费率字段序列化统一（保留两位小数）
  - 痛点：部分接口返回 `Decimal`，部分转字符串，存在不一致与 JSON 编码隐患。
  - 变更
    - 统一金额类字段在响应中转字符串，保留两位（例如 `quantize(0.01)`）。
    - 在 `build_response` 或统一的 `json_encoders` 中集中处理。
  - 验收
    - 金额、费率、CPL 等字段格式统一，前端无需特判。

- [ ] 系统边界统一（选型确认与落地计划）
  - 痛点：前端读取直连 Supabase，写入走 FastAPI，双入口易产生数据/权限不一致。
  - 变更（选型二选一）
    - A：后端中台化（BFF）：前端统一经 FastAPI 读写；Supabase 仅鉴权/存储；业务逻辑与审计集中在后端。
    - B：Supabase-first：业务规则下沉至数据库（RLS/函数/触发器），前端统一用 Supabase SDK 访问；减少重叠后端接口。
  - 验收：全功能路径统一到单一数据通道；文档与代码同步调整。

## P1 稳定性与一致性

- [ ] 懒加载数据库引擎 + 测试环境兜底
  - 痛点：`backend/core/db.py` 导入期即创建 engine，环境变量缺失即崩；与内存 SQLite 测试耦合。
  - 变更
    - 将 engine 创建改为懒加载（首次获取 Session 时初始化）。
    - 提供 `.env.example`；测试环境优先采用 SQLite 或改为 Docker Postgres。
  - 验收
    - 无数据库变量时导入不崩；测试可独立运行。

- [ ] 接口鉴权与 CORS 限制
  - 痛点：API 无鉴权；CORS 为 `*`。
  - 变更
    - 新增 Supabase JWT 校验依赖（读取 Authorization: Bearer，验证后将用户注入请求上下文）。
    - 生产环境将 `allowed_origins` 改为白名单 ENV。
  - 验收
    - 未携带/无效 Token 拒绝访问受保护路由；跨域限制符合配置。

- [ ] 列表接口分页/过滤
  - 变更
    - `GET /api/projects|channels|topups` 添加 `page/size` 与必要过滤项。
  - 验收
    - 大数据量下响应稳定，前端能分页加载。

- [ ] 去重 `build_response`
  - 变更
    - 将 `build_response` 抽到 `backend/core/response.py`，各路由统一调用。
  - 验收
    - 路由不再重复定义该函数。

- [ ] 数据一致性与事务保证
  - [ ] CPL/手续费派生值重算机制：当源值变更（spend/leads/fee 配置）时自动重算（触发器/服务层保障），避免派生值失真。
  - [ ] Topup 状态机并发保护：采用乐观锁（基于 `updated_at`）或条件更新（WHERE status=旧值）保证转移原子性。
  - [ ] 多币种一致性：报表与对账聚合明确币种维度，必要时引入汇率表与换汇策略。

- [ ] 前后端数据边界统一（选型落地）
  - 变更：根据 P0 选型结果，替换直连 Supabase 的页面数据来源或退场重叠后端接口；补齐鉴权与审计。

## P1 工程化与运维

- [ ] 固定依赖版本 + 单一包管理器
  - 痛点：`package.json` 依赖大量 `"latest"`；存在 `package-lock.json` 与 `pnpm-lock.yaml` 双锁。
  - 变更
    - 锁定 Next/React/Supabase 兼容版本；仅保留一个锁文件；配置 Renovate/Dependabot 自动 PR。
  - 验收
    - 干净安装后构建可复现；无锁文件冲突。

- [ ] 后端依赖清单与数据库迁移
  - 变更
    - 增加 `pyproject.toml` 或 `requirements.txt`（FastAPI、Uvicorn、SQLAlchemy、Pydantic、psycopg、python-jose 等）。
    - 初始化 Alembic，提交初始迁移。
  - 验收
    - 新环境可一键安装 + 迁移成功。

- [ ] Docker 化与启动脚本
  - 变更
    - 提供后端 Dockerfile + docker-compose（API + Postgres）；前端 `.env.local.example` 与后端 `.env.example`。
  - 验收
    - `docker compose up` 可一键拉起完整环境。

## P2 代码质量与测试

- [ ] SQLAlchemy 2.0 风格与类型标注
  - 变更
    - 查询改为 `select()` 风格；为 Session、返回值、payload 增加类型注解。
  - 验收
    - 代码更一致、类型提示完整。

- [ ] 日志与审计增强
  - 变更
    - 请求链路注入 Correlation-Id；关键写操作统一记录 `actor_id/IP`；结构化日志（JSON）。
  - 验收
    - 操作轨迹完整可追溯；错误分级清晰。

- [ ] 测试覆盖
  - 变更
    - 单元测试：CPL 计算、手续费计算、状态机（Topup）、异常包裹。
    - 集成测试：鉴权、跨实体一致性、分页。
  - 验收
    - 关键路径覆盖率达标（>80%），PR 阶段自动跑测试。

## P1 存储与类型（与测试/部署协同）

- [ ] 单一数据源确认
  - 变更：后端直连 Supabase PG，避免多库；环境与凭据统一管理。
  - 验收：线上/测试/本地一致性明确。

- [ ] 方言差异与测试偏差消除
  - 变更：改为 Postgres 测试（Docker）或降低方言耦合；迁移脚本齐备。
  - 验收：避免“本地测得过、线上挂”的方言差异。

## P1 查询性能与可扩展性

- [ ] 报表索引与预聚合
  - 变更：为日期、外键维度建立复合索引；月度统计使用物化视图或预聚合表（定时刷新）。
  - 验收：数据量增长后查询稳定、SLA 满足。

## P1 可运维性与可观测性

- [ ] 统一响应契约与日志落盘
  - 变更：全局异常处理（同上）；服务级结构化日志；错误分级与报警规则。
  - 验收：日志可检索、可关联（request-id），报警准确。

## P1 部署与环境

- [ ] 域名/地区统一与网关
  - 变更：前后端域名与地区统一（降低跨区延迟）；对外提供反向代理或 API 网关统一入口；CORS 与鉴权策略集中管理。
  - 验收：延迟与跨域问题收敛，配置集中可控。

## 里程碑与实施顺序

- M1（1–2 天，P0）
  - 统一响应与异常处理
  - API Base URL 规范与文档修正
  - Topup 关联校验
  - 金额字段序列化统一
  - 系统边界选型定案（后端中台化 或 Supabase-first）

- M2（2–3 天，P1）
  - 懒加载 DB / 测试兜底
  - 鉴权与 CORS 收紧（JWT + RBAC）
  - 列表分页/过滤、抽离 `build_response`
  - 数据一致性：CPL/手续费重算、Topup 乐观锁；币种维度处理
  - 边界选型落地（替换直连/退场重叠接口）

- M3（2–4 天，P1/P2）
  - 依赖锁定与单一包管
  - 后端依赖与 Alembic、Docker 化
  - SQLAlchemy 2.0、类型补全、测试补齐
  - 报表索引/物化视图、日志追踪与报警、部署统一

## 回滚与兼容策略

- 保持接口路径不变；仅调整响应结构与新增分页参数。
- 新鉴权逻辑用 Feature Flag 灰度；支持回滚。
- 提供迁移回滚脚本；先双写再切换，避免破坏性删除。

## 附：示例代码骨架

- 全局异常处理（示意）
```python
# backend/core/response.py
from datetime import datetime, timezone
from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class ApiResponse(BaseModel, Generic[T]):
    data: Optional[T]
    error: Optional[str]
    meta: dict[str, Any]

def ok(data: Any) -> dict:
    return {"data": data, "error": None, "meta": {"timestamp": datetime.now(tz=timezone.utc).isoformat()}}

def fail(error: str, data: Any = None) -> dict:
    return {"data": data, "error": error, "meta": {"timestamp": datetime.now(tz=timezone.utc).isoformat()}}
```

```python
# backend/main.py 片段
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from core.response import fail

@app.exception_handler(HTTPException)
async def http_exc_handler(_: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content=fail(str(exc.detail)))

@app.exception_handler(Exception)
async def unhandled_exc_handler(_: Request, exc: Exception):
    return JSONResponse(status_code=500, content=fail("Internal server error"))
```

- Topup 关联校验（示意）
```python
# backend/routers/topups.py 片段
account = db.query(AdAccount).filter(AdAccount.id == payload.ad_account_id).first()
if not account:
    raise HTTPException(status_code=404, detail="Ad account not found")
if account.project_id != payload.project_id or account.channel_id != payload.channel_id:
    raise HTTPException(status_code=422, detail="Account/project/channel mismatch")
```

- 前端 API Base URL 规范（示意）
```ts
// lib/api.ts 片段
const raw = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const normalized = raw.replace(/\/+$/, "").replace(/\/api$/, "");
const API_BASE_URL = normalized;

export async function apiFetch<T>(path: string, options: RequestInit = {}) {
  const url = `${API_BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;
  const res = await fetch(url, { ...options, headers: { "Content-Type": "application/json", ...options.headers } });
  let payload: any = null;
  try { payload = await res.json(); } catch { /* 忽略非 JSON */ }
  if (!res.ok) {
    const error = payload?.error ?? payload?.detail ?? res.statusText;
    return { data: null, error, meta: null };
  }
  if (typeof payload !== "object" || payload === null || !("data" in payload) || !("error" in payload)) {
    return { data: null, error: "响应结构无效", meta: null };
  }
  return payload;
}
```

## 补充项（二次审视新增）

### P0 补充

- [ ] 统一金额四舍五入策略
  - 说明：当前 CPL 与手续费使用的四舍五入方式不一致（如 ROUND_HALF_UP vs 默认）。
  - 动作：统一所有金钱类字段的四舍五入策略（建议统一为 ROUND_HALF_UP），在后端集中实现并文档化，前端展示保持两位小数。

- [ ] 日期与时区统一
  - 说明：前端使用 `toISOString().slice(0,10)` 可能因 UTC 偏差导致“日期前后错位”。
  - 动作：统一“业务时区”或明确全部使用 UTC；前端选择器与显示按业务时区处理；后端以 UTC 存储；报表/区间口径统一说明。

### P1 补充

- [ ] API 版本化
  - 动作：引入 `/api/v1` 路径前缀并规划升级与兼容策略，网关/反代层辅助路由切换。

- [ ] RBAC 与对象级权限
  - 动作：定义角色矩阵（投手/户管/财务/管理员）与对象级权限（项目/账户归属），在后端统一强制校验并与审计联动。

- [ ] 敏感信息与安全响应
  - 动作：生产环境错误信息“泛化”，避免泄漏栈与 SQL；日志/审计对邮箱、IP 等脱敏或分级存储。

- [ ] 安全头与 CSP
  - 动作：在 Next.js 设置严格安全头（CSP、HSTS、X-Frame-Options、Referrer-Policy、Permissions-Policy）。

- [ ] 速率限制与幂等
  - 动作：关键写接口添加 Rate Limit；支持 Idempotency-Key（日报/充值），409 时返回资源信息，减少重复提交影响。

- [ ] 健康与就绪探针/指标
  - 动作：区分 `/healthz`（存活）与 `/readyz`（包含 DB 连通、迁移版本、外部依赖）；暴露 Prometheus `/metrics` 请求量/错误/时延。

- [ ] 结构化日志与 Trace
  - 动作：引入 Correlation-Id/Request-Id；可选集成 OpenTelemetry，便于问题溯源与性能分析。

- [ ] 必备索引策略
  - 动作：
    - AdSpendDaily：(`ad_account_id`,`date`)、`user_id`、`date` 相关复合索引；
    - Topup：`channel_id`,`created_at`,`status`；
    - Ledger：`project_id`,`occurred_at`；
    - 报表常用 JOIN/过滤字段建立覆盖索引。

- [ ] 真机 Postgres 测试
  - 动作：CI 使用 docker-compose 启动 Postgres，执行迁移与测试，消除 SQLite 方言偏差。

- [ ] 多币种聚合与换汇
  - 动作：报表/对账按币种维度聚合；需要跨币种时引入汇率表与换汇规则（时点/日均/月均）并固定口径。

- [ ] 派生值重算触发器
  - 动作：当 spend/leads/fee 配置变更时，触发器或服务层自动重算 CPL/手续费，保障派生值一致性。

- [ ] 并发状态转移条件更新
  - 动作：Topup 状态转移使用条件更新（WHERE id=? AND status=?）或乐观锁（基于 `updated_at`），失败返回 409 并提示冲突信息。

- [ ] 幂等创建
  - 动作：日报与 Topup 支持幂等键（如 account+date）或幂等请求头，避免重复创建与 409 体验差。

### P2 补充

- [ ] API 语义与错误码规范
  - 动作：统一方法/路径语义（如 PATCH `/ad-accounts/{id}/status`）；分页/排序参数；标准化 `error_code` 与 `error_message`。

- [ ] OpenAPI 与调试集合
  - 动作：完善 FastAPI 文档与说明，提供示例 curl 和 Postman/Thunder 集合，便于联调与验收。

- [ ] 运行参数与资源限制
  - 动作：明确 Uvicorn/Gunicorn 进程模型、超时与 body 限制、数据库连接池上限等运行参数。

- [ ] 前端输入校验与 UX
  - 动作：金额/数量输入强校验与本地格式化（两位小数、非负）；提交按钮禁用与重试提示；可预防重复提交。

- [ ] i18n 与 A11y
  - 动作：最小化多语言支持与可访问性增强（aria 标签、对比度、键盘操作）。

- [ ] 错误展示一致性
  - 动作：统一 Toast/提示条组件，将 `error_code` 映射为本地化消息，前后端错误信息一致对齐。
