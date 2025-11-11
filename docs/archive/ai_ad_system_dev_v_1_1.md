# AI广告代投系统开发文档 v1.1 修订版

> 本文档在 v1.0 基础上修订，针对接口一致性、状态机定义、权限体系、日志机制、AI 模块入口、数据库结构等关键问题进行了优化，以便架构师、Cursor 或任何开发成员能直接使用。

---

## 一、文档结构概览

- **SYSTEM_OVERVIEW.md**：系统概述与架构
- **BACKEND_API_GUIDE.md**：后端接口与模型定义
- **FRONTEND_GUIDE.md**：前端组件与接口调用逻辑
- **DEPLOYMENT_GUIDE.md**：部署与环境配置
- **DATA_SCHEMA.md**：数据库与字段约束
- **STATE_MACHINE.md**：核心流程状态流转与操作角色

---

## 二、系统架构

### 1. 架构层次
```
Next.js (前端)
  → REST API (FastAPI)
  → SQLAlchemy ORM (数据访问层)
  → PostgreSQL (Supabase 托管)
  → Storage + RLS 安全策略
```

### 2. 主要服务组件
| 模块 | 技术栈 | 功能 |
|------|---------|------|
| 前端 | Next.js + TS + Tailwind | 表单录入、分析展示、权限控制 |
| 后端 | FastAPI + SQLAlchemy | 核心逻辑、API接口、AI预测引擎 |
| 数据库 | Supabase PostgreSQL | 存储核心业务数据 |
| 缓存 | Redis | 异步任务队列、预测缓存 |
| 日志 | Loki + Promtail | 操作日志与审计记录 |

---

## 三、状态机定义

### 1. 充值申请状态流
| 状态 | 描述 | 可操作角色 | 下一状态 |
|------|------|-------------|------------|
| draft | 投手提交申请 | 投手 | pending |
| pending | 户管审核中 | 户管 | approved / rejected |
| approved | 财务审批通过 | 财务 | paid |
| paid | 财务执行充值 | 系统 | posted |
| posted | 已完成记账 | 系统 | — |
| rejected | 审批拒绝 | 户管/财务 | draft（修改后重提） |

### 2. 日报状态流
| 状态 | 描述 | 可操作角色 | 下一状态 |
|------|------|-------------|------------|
| draft | 投手录入 | 投手 | pending |
| pending | 待审核 | 数据员 | approved / rejected |
| approved | 审核通过 | 系统 | — |
| rejected | 数据异常 | 数据员 | draft |

### 3. 账户生命周期
| 状态 | 说明 | 自动触发条件 |
|------|------|----------------|
| new | 新建账户 | 户管创建 |
| testing | 测试期账户 | 前7天无异常 |
| active | 正常投放中 | 日均消耗>100USD |
| suspended | 暂停投放 | 3天无消耗 |
| dead | 被封禁或失效 | Facebook API反馈 |
| archived | 已归档 | 管理员手动 |

---

## 四、数据库结构优化

### 1. 核心表结构统一规则
- 所有表字段必须包含：`id`, `created_at`, `updated_at`。
- 金额字段统一类型：`NUMERIC(15,2)`。
- 外键均设置：`ON DELETE SET NULL`（保留历史数据）。

### 2. 外键追溯约束
```
所有资金或消耗相关表（topups、ad_spend_daily、reconciliation）必须包含：
project_id NOT NULL
ad_account_id NOT NULL
user_id NOT NULL
```

### 3. 关键新增表
| 表名 | 作用 |
|------|------|
| `ledgers` | 财务流水，记录所有交易与费用分摊 |
| `logs` | 操作日志，记录每次接口调用与状态变更 |
| `import_jobs` | 数据导入任务表，记录导入来源与结果 |
| `reconciliations` | 对账结果记录表 |

### 4. 示例表定义（Topups）
```sql
CREATE TABLE public.topups (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  ad_account_id uuid NOT NULL REFERENCES ad_accounts(id),
  user_id uuid NOT NULL REFERENCES users(id),
  amount NUMERIC(15,2) NOT NULL,
  fee_rate NUMERIC(5,2),
  status VARCHAR(20) DEFAULT 'draft',
  approved_by uuid REFERENCES users(id),
  paid_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

---

## 五、接口规范

### 1. 命名与风格
- 路由使用 kebab-case：`/api/topups/request`
- HTTP 动作：GET 查询、POST 创建、PUT 更新、DELETE 删除
- 返回格式：`{ data, error, message }`
- 所有接口需在返回头中附带 `X-Request-ID` 追踪号

### 2. 示例接口
```python
@router.post('/topups/request')
def create_topup(req: TopupCreateSchema, user: User = Depends(auth_user)):
    with session.begin():
        topup = Topup(**req.dict(), user_id=user.id)
        session.add(topup)
        log_action('topup', 'create', user.id, topup.id)
    return {"data": topup, "message": "Recharge request created."}
```

### 3. 日志与异常捕获
```python
try:
    ... # 业务逻辑
except Exception as e:
    log_action('system', 'error', user.id, str(e))
    raise HTTPException(status_code=500, detail="Internal Server Error")
```

---

## 六、权限矩阵
| 模块/功能 | 投手 | 户管 | 财务 | 管理员 |
|------------|------|------|------|----------|
| 日报提交 | ✅ | ✅ | ❌ | ✅ |
| 日报审核 | ❌ | ✅ | ❌ | ✅ |
| 充值申请 | ✅ | ✅ | ✅ | ✅ |
| 审批充值 | ❌ | ❌ | ✅ | ✅ |
| 项目编辑 | ❌ | ✅ | ❌ | ✅ |
| 用户管理 | ❌ | ❌ | ❌ | ✅ |
| 对账操作 | ❌ | ❌ | ✅ | ✅ |

---

## 七、AI 模块设计

### 1. 模块接口
```python
class AIPredictor:
    def predict_lifetime(self, account_id: str) -> dict:
        # 返回账户剩余寿命预测
        return {"days_remaining": 12, "risk_level": "medium"}

    def detect_anomaly(self, spend_data: list) -> list:
        # 检测日报异常
        return [{"date": "2025-11-10", "reason": "消耗异常波动"}]
```

### 2. 应用场景
- 自动预警死户：在账户状态变更任务中调用 `predict_lifetime`
- 异常日报标注：日报审核阶段调用 `detect_anomaly`

---

## 八、部署与安全

### 1. 环境管理
- `.env.docker`：容器内部配置（Supabase、Redis、SMTP）
- `.env.local`：本地开发配置
- 不可上传密钥到 Git

### 2. 日志与监控
- Loki + Promtail：日志收集
- Prometheus + Grafana：性能监控
- Sentry：错误上报

### 3. 定时任务
```bash
0 3 * * * /app/scripts/backup.sh >> /var/log/backup.log 2>&1
```

### 4. Docker 优化
```dockerfile
COPY --from=frontend-builder /app/.next ./frontend_build
```

---

## 九、开发计划（修订版）
| 阶段 | 时间 | 目标 |
|------|------|------|
| 第一阶段 | 2周 | 核心模块开发：项目、渠道、账户、日报、充值 |
| 第二阶段 | 2周 | 财务模块、自动对账、日志体系 |
| 第三阶段 | 2周 | 数据分析、AI 异常检测、寿命预测 |
| 第四阶段 | 1周 | 部署优化、安全与监控 |

---

## 十、验收标准
- ✅ 所有核心流程（日报、充值、对账）均可端到端执行
- ✅ 所有API均具备事务与日志
- ✅ RLS策略生效
- ✅ Prometheus可监控关键指标
- ✅ 系统错误率 < 1%

---

**版本**: v1.1  
**更新时间**: 2025-11-10  
**维护人**: 系统架构负责人

