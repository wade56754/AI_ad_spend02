# BR-DATA: 数据质量与完整性规则

> **文档版本**: v1.0
> **最后更新**: 2025-11-20
> **所属模块**: 数据管理 (Data Management)
> **引用文档**:
> - `DATA_SCHEMA.md` - 数据结构定义
> - `ERROR_CODES.md` - 错误码定义
> - `STATE_MACHINE.md` - 状态机定义
> - `AI_AD_SYSTEM_MASTER_SPEC_v2.2.md` - 核心开发手册 (第 3.3, 4.3 节)

---

## 规则概览

| 规则编号 | 规则名称 | 优先级 | 状态 |
|---------|---------|--------|------|
| BR-DATA-001 | 外键完整性与删除策略 | P0 | ✅ Active |
| BR-DATA-002 | 时间字段一致性规范 | P0 | ✅ Active |

---

## BR-DATA-001: 外键完整性与删除策略

### 业务场景

AI广告代投系统涉及项目、广告账户、充值申请、日报等核心业务数据，这些数据之间存在复杂的关联关系。为了保证数据完整性和可追溯性，系统必须禁止物理删除核心业务记录，而是通过状态机流转至终态 (`archived`, `cancelled`) 实现逻辑删除。

### 规则定义

#### 1.1 禁止物理删除的实体

**引用**: `AI_AD_SYSTEM_MASTER_SPEC_v2.2.md` 第 5.2.1 节 - 禁止物理删除原则

以下核心业务实体**严禁物理删除** (`DELETE` 操作):

| 实体表 | 主键类型 | 终态 | 删除策略 | 说明 |
|-------|---------|------|---------|------|
| `users` | UUID | `is_active=false` | 逻辑删除 | 用户禁用而非删除,保留审计日志 |
| `projects` | BIGSERIAL | `archived` | 逻辑删除 | 项目归档后禁止编辑,可查看历史 |
| `ad_accounts` | BIGSERIAL | `archived` | 逻辑删除 | 账户归档后禁止提交日报 |
| `daily_reports` | BIGSERIAL | `approved`, `rejected` | 逻辑删除 | 终态后禁止编辑,可重新提交 |
| `topup_requests` | BIGSERIAL | `completed`, `cancelled`, `rejected` | 逻辑删除 | 终态后禁止修改,保留财务记录 |
| `ledger_entries` | BIGSERIAL | - | 禁止删除 | 资金总账永久保留 |
| `reconciliation_batches` | BIGSERIAL | `completed`, `cancelled` | 逻辑删除 | 对账批次完成后不可删除 |

**允许物理删除的实体**:
- 临时数据: `user_sessions` (会话过期后自动清理)
- 缓存数据: `import_job_cache` (定期清理)
- 测试数据: 开发/测试环境可物理删除

#### 1.2 外键约束与删除策略

**引用**: `DATA_SCHEMA.md` 第 3.3 节 - 外键完整性约束

**ON DELETE 策略选择**:

| 策略 | 适用场景 | 示例 |
|-----|---------|------|
| **RESTRICT** | 禁止删除被引用记录 | 禁止删除有日报的广告账户,禁止删除有充值申请的项目 |
| **CASCADE** | 级联删除关联记录 | 删除项目时级联删除项目成员 (`project_members`) |
| **SET NULL** | 设置为 NULL | 户管离职时,投手的 `account_manager_id` 设为 NULL |
| **SET DEFAULT** | 设置为默认值 | 极少使用 |

**关键外键约束示例**:

```sql
-- ✅ 正确: 禁止删除有日报的广告账户
CREATE TABLE daily_reports (
    id BIGSERIAL PRIMARY KEY,
    ad_account_id BIGINT NOT NULL REFERENCES ad_accounts(id) ON DELETE RESTRICT,
    -- 其他字段...
);

-- ✅ 正确: 禁止删除有充值申请的项目
CREATE TABLE topup_requests (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES projects(id) ON DELETE RESTRICT,
    -- 其他字段...
);

-- ✅ 正确: 户管离职时投手不被删除
CREATE TABLE users (
    id UUID PRIMARY KEY,
    account_manager_id UUID REFERENCES users(id) ON DELETE SET NULL,
    -- 其他字段...
);

-- ✅ 正确: 删除项目时级联删除项目成员
CREATE TABLE project_members (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    -- 其他字段...
);

-- ❌ 错误: 不应该使用 CASCADE 删除核心业务数据
CREATE TABLE topup_requests (
    project_id BIGINT NOT NULL REFERENCES projects(id) ON DELETE CASCADE  -- 禁止!
);
```

#### 1.3 逻辑删除实现规范

**方案一: 状态字段标记**

```python
# ✅ 正确: 通过状态机流转实现逻辑删除
@router.post("/projects/{project_id}/archive")
async def archive_project(
    project_id: int,
    service: ProjectService = Depends(),
    current_user: Dict = Depends(require_role(["admin", "account_manager"]))
):
    """归档项目 (逻辑删除)"""
    project = service.archive_project(project_id, current_user)
    return success_response(
        data=ProjectResponse.model_validate(project),
        message="项目已归档"
    )

# Service 层实现
class ProjectService:
    def archive_project(self, project_id: int, user: Dict) -> Project:
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ResourceNotFoundException(
                code=BusinessErrorCodes.RESOURCE_NOT_FOUND.code,
                message=f"项目 {project_id} 不存在"
            )

        # 业务规则检查: 归档前确保无未完成的充值申请
        pending_topups = self.db.query(TopupRequest).filter(
            TopupRequest.project_id == project_id,
            TopupRequest.status.notin_(["completed", "cancelled", "rejected"])
        ).count()

        if pending_topups > 0:
            raise BusinessRuleException(
                code=BusinessErrorCodes.INVALID_OPERATION.code,
                message=f"项目还有 {pending_topups} 个未完成的充值申请,无法归档"
            )

        # 执行逻辑删除
        with self.db.begin():
            project.status = "archived"
            project.updated_at = datetime.now(timezone.utc)
            project.updated_by = user.get("user", {}).id

            # 记录审计日志
            self._create_audit_log(
                action="ARCHIVE_PROJECT",
                entity_id=str(project.id),
                user=user,
                payload_before={"status": project.status},
                payload_after={"status": "archived"}
            )

        return project

# ❌ 错误: 物理删除
@router.delete("/projects/{project_id}")
async def delete_project(project_id: int):
    db.query(Project).filter(Project.id == project_id).delete()  # 禁止!
    db.commit()
```

**方案二: is_deleted 字段 (备用方案)**

对于没有状态机的表 (如 `channels`)，可使用 `is_deleted` 字段:

```sql
CREATE TABLE channels (
    id UUID PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMPTZ,
    deleted_by UUID REFERENCES users(id)
);

-- 查询时过滤已删除记录
SELECT * FROM channels WHERE is_deleted = FALSE;
```

#### 1.4 级联归档规则

**规则**: 父实体归档时,检查子实体状态,必要时级联归档。

**示例**:
```python
class ProjectService:
    def archive_project(self, project_id: int, user: Dict) -> Project:
        # 1. 检查并归档所有活跃的广告账户
        active_accounts = self.db.query(AdAccount).filter(
            AdAccount.project_id == project_id,
            AdAccount.status != "archived"
        ).all()

        for account in active_accounts:
            if account.status in ["active", "testing"]:
                # 级联归档广告账户
                account.status = "archived"
                account.updated_at = datetime.now(timezone.utc)
                self._create_audit_log(
                    action="CASCADE_ARCHIVE_ACCOUNT",
                    entity_id=str(account.id),
                    user=user,
                    notes=f"项目 {project_id} 归档时自动归档"
                )

        # 2. 归档项目本身
        project.status = "archived"
        # ...
```

### 错误码映射

| 场景 | 错误码 | HTTP状态码 | 错误消息示例 |
|-----|--------|-----------|------------|
| 尝试物理删除核心数据 | `DB_005` | 400 | "禁止物理删除项目,请使用归档功能" |
| 外键约束违反 | `DB_001` | 400 | "无法删除项目,存在关联的充值申请" |
| 终态记录无法修改 | `BIZ_001` | 400 | "项目已归档,无法编辑" |
| 级联检查失败 | `BIZ_001` | 400 | "项目还有 3 个活跃的广告账户,无法归档" |

**引用**: `ERROR_CODES.md` - 数据库错误码 (DB_*), 业务错误码 (BIZ_*)

### 测试用例 (Test Intent)

**TC-DATA-001-01: 项目归档成功**
- **Given**: 项目 #101 状态为 `active`, 无未完成的充值申请, 所有广告账户已归档
- **When**: 客户经理调用 `/projects/101/archive`
- **Then**:
  - `projects.status` 更新为 `archived`
  - `updated_at` 更新为当前UTC时间
  - 审计日志记录归档操作

**TC-DATA-001-02: 归档前检查失败 (有未完成充值)**
- **Given**: 项目 #102 有 2 个状态为 `pending_review` 的充值申请
- **When**: 尝试归档项目 #102
- **Then**: 返回 HTTP 400, 错误码 `BIZ_001`, 消息 "项目还有 2 个未完成的充值申请,无法归档"

**TC-DATA-001-03: 级联归档广告账户**
- **Given**: 项目 #103 有 3 个状态为 `active` 的广告账户
- **When**: 归档项目 #103
- **Then**:
  - 项目状态更新为 `archived`
  - 3 个广告账户状态自动更新为 `archived`
  - 审计日志记录 4 条操作 (1个项目 + 3个账户)

**TC-DATA-001-04: 尝试物理删除项目 (API禁止)**
- **Given**: 项目 #104 存在
- **When**: 调用 `DELETE /projects/104` (假设存在此接口)
- **Then**: 返回 HTTP 400, 错误码 `DB_005`, 消息 "禁止物理删除项目,请使用归档功能"

**TC-DATA-001-05: 外键约束防止误删**
- **Given**: 项目 #105 有 5 条日报记录
- **When**: 数据库层尝试执行 `DELETE FROM projects WHERE id = 105`
- **Then**:
  - 数据库返回外键约束错误 (RESTRICT)
  - 项目未被删除

**TC-DATA-001-06: 用户禁用 (逻辑删除)**
- **Given**: 用户 Alice (user_id=U1, role=media_buyer)
- **When**: 管理员调用 `/users/U1/disable`
- **Then**:
  - `users.is_active` 更新为 `false`
  - Alice 无法登录
  - Alice 的历史数据 (日报、充值申请) 保留

**TC-DATA-001-07: 户管离职 (SET NULL)**
- **Given**: 户管 Bob (user_id=U2) 管理 10 个投手
- **When**: 管理员禁用 Bob 的账户
- **Then**:
  - 10 个投手的 `account_manager_id` 设为 NULL
  - 投手仍可正常使用系统
  - 需手动重新分配户管

---

## BR-DATA-002: 时间字段一致性规范

### 业务场景

系统需要处理跨时区用户和全球广告平台的时间数据。为了避免时区混乱导致的数据错误 (如日报日期错误、审批时效计算错误)，系统必须在数据库层、应用层、展示层统一时间处理规范。

### 规则定义

#### 2.1 数据库层规范

**引用**: `DATA_SCHEMA.md` 第 3.2.2 节 - 时间字段规范

**强制要求**:
- ✅ 所有时间字段必须使用 `TIMESTAMPTZ` (带时区的时间戳)
- ✅ 默认值使用 `NOW()` 函数 (返回UTC时间)
- ❌ 禁止使用 `TIMESTAMP` (不带时区,易混淆)
- ❌ 禁止使用 `DATE` 存储时间戳 (精度丢失)

**字段类型对照**:

| 场景 | 正确类型 | 错误类型 | 说明 |
|-----|---------|---------|------|
| 创建时间 | `TIMESTAMPTZ` | `TIMESTAMP` | 需要记录时区信息 |
| 更新时间 | `TIMESTAMPTZ` | `TIMESTAMP` | 需要记录时区信息 |
| 业务日期 | `DATE` | `TIMESTAMPTZ` | 不含时区的日期 (如日报日期) |
| 审批时间 | `TIMESTAMPTZ` | `TIMESTAMP` | 需要记录时区信息 |

**示例**:
```sql
-- ✅ 正确: 使用 TIMESTAMPTZ
CREATE TABLE daily_reports (
    id BIGSERIAL PRIMARY KEY,
    report_date DATE NOT NULL,  -- 业务日期 (无时区)
    created_at TIMESTAMPTZ DEFAULT NOW(),  -- 创建时间 (UTC)
    updated_at TIMESTAMPTZ DEFAULT NOW(),  -- 更新时间 (UTC)
    submitted_at TIMESTAMPTZ,  -- 提交时间 (可空)
    approved_at TIMESTAMPTZ    -- 审批时间 (可空)
);

-- 触发器: 自动更新 updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_daily_reports_updated_at
    BEFORE UPDATE ON daily_reports
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ❌ 错误: 使用 TIMESTAMP (无时区)
CREATE TABLE daily_reports (
    created_at TIMESTAMP DEFAULT NOW()  -- 禁止!
);
```

#### 2.2 应用层规范 (Python Backend)

**引用**: `AI_AD_SYSTEM_MASTER_SPEC_v2.2.md` 第 4.3.2 节 - 后端时间处理

**强制要求**:
- ✅ 统一使用 `datetime.now(timezone.utc)` 获取当前UTC时间
- ✅ API响应使用 ISO 8601 格式 (含时区标识 `Z`)
- ❌ 禁止使用 `datetime.now()` (无时区信息)
- ❌ 禁止使用本地时区 (`datetime.now(timezone('Asia/Shanghai'))`)

**代码示例**:
```python
from datetime import datetime, timezone, date
from pydantic import BaseModel, Field

# ✅ 正确: 获取UTC时间
now = datetime.now(timezone.utc)

# ❌ 错误: 无时区信息
now = datetime.now()  # 禁止!

# ✅ 正确: Pydantic Schema
class DailyReportCreate(BaseModel):
    report_date: date  # 业务日期 (不含时区)
    spend: Decimal

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()  # 转换为 ISO 8601 格式
        }

# ✅ 正确: SQLAlchemy Model
from sqlalchemy import Column, DateTime, Date
class DailyReport(Base):
    __tablename__ = "daily_reports"
    report_date = Column(Date, nullable=False)  # 业务日期
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "report_date": self.report_date.isoformat(),  # 2025-11-20
            "created_at": self.created_at.isoformat(),  # 2025-11-20T10:30:00+00:00
        }

# ✅ 正确: Service 层
class DailyReportService:
    def create_report(self, payload: DailyReportCreate, user: Dict) -> DailyReport:
        now = datetime.now(timezone.utc)  # UTC时间

        report = DailyReport(
            report_date=payload.report_date,
            spend=payload.spend,
            created_at=now,
            updated_at=now,
            created_by=user.get("user", {}).id
        )

        self.db.add(report)
        self.db.commit()
        return report
```

**API响应示例**:
```json
{
  "success": true,
  "data": {
    "id": 12345,
    "report_date": "2025-11-20",
    "created_at": "2025-11-20T10:30:00Z",
    "submitted_at": "2025-11-20T11:45:00Z"
  },
  "timestamp": "2025-11-20T12:00:00Z"
}
```

#### 2.3 前端展示层规范 (TypeScript Frontend)

**引用**: `AI_AD_SYSTEM_MASTER_SPEC_v2.2.md` 第 4.3.3 节 - 前端时区转换

**核心原则**: 前端负责将UTC时间转换为用户本地时区显示。

**推荐库**: `date-fns` + `date-fns-tz`

```bash
pnpm add date-fns date-fns-tz
```

**代码示例**:
```typescript
// lib/datetime.ts
import { format, parseISO } from 'date-fns';
import { formatInTimeZone } from 'date-fns-tz';

/**
 * 将UTC时间转换为用户本地时区显示
 */
export function formatUTCToLocal(
  utcDateString: string,
  formatString: string = 'yyyy-MM-dd HH:mm:ss'
): string {
  // 获取用户浏览器时区
  const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

  // 转换为本地时区
  return formatInTimeZone(
    parseISO(utcDateString),
    userTimezone,
    formatString
  );
}

/**
 * 将本地时间转换为UTC发送给后端
 */
export function formatLocalToUTC(localDate: Date): string {
  return localDate.toISOString();  // 自动转换为UTC
}

// ✅ 使用示例
const utcTime = "2025-11-20T10:30:00Z";
const localTime = formatUTCToLocal(utcTime);
// 输出: "2025-11-20 18:30:00" (假设用户在 Asia/Shanghai 时区)
```

**React组件示例**:
```typescript
// components/DateTimeDisplay.tsx
interface DateTimeDisplayProps {
  utcDateString: string;
  showRelative?: boolean;
}

export function DateTimeDisplay({ utcDateString }: DateTimeDisplayProps) {
  return <span>{formatUTCToLocal(utcDateString)}</span>;
}

// 使用
<DateTimeDisplay utcDateString="2025-11-20T10:30:00Z" />
// 显示: 2025-11-20 18:30:00
```

#### 2.4 时区相关业务规则

**引用**: `AI_AD_SYSTEM_MASTER_SPEC_v2.2.md` 第 4.3.4 节 - 时区相关业务规则

| 场景 | 处理方式 | 示例 |
|-----|---------|------|
| **日报截止时间** | 以项目配置的时区为准 | 项目时区为 `Asia/Shanghai`, 每日 23:59:59 之前可提交 |
| **充值审批时效** | 后端计算时间差,不受时区影响 | 72小时内必须审批 (基于UTC时间戳) |
| **对账周期** | 以自然月为单位,使用项目时区 | 2025年11月对账 = 2025-11-01 00:00:00 ~ 2025-11-30 23:59:59 (项目时区) |
| **审计日志** | 统一显示UTC时间 + 本地时间 | `created_at: 2025-11-20T10:30:00Z (本地: 2025-11-20 18:30:00)` |

**业务规则实现**:
```python
# backend/services/daily_report_service.py
class DailyReportService:
    def check_deadline(self, report_date: date, project: Project) -> bool:
        """检查日报是否在截止时间前提交"""
        # 获取项目时区 (默认 Asia/Shanghai)
        project_timezone = pytz.timezone(project.timezone or "Asia/Shanghai")

        # 计算截止时间 (report_date 23:59:59 项目时区)
        deadline_local = project_timezone.localize(
            datetime.combine(report_date, datetime.max.time())
        )
        deadline_utc = deadline_local.astimezone(pytz.UTC)

        # 当前UTC时间
        now_utc = datetime.now(timezone.utc)

        # 判断是否超期
        if now_utc > deadline_utc:
            raise BusinessRuleException(
                code=BusinessErrorCodes.DEADLINE_EXCEEDED.code,
                message=f"日报提交已超过截止时间 ({deadline_local.strftime('%Y-%m-%d %H:%M:%S')} {project.timezone})"
            )

        return True
```

### 错误码映射

| 场景 | 错误码 | HTTP状态码 | 错误消息示例 |
|-----|--------|-----------|------------|
| 时间字段类型错误 | `BIZ_002` | 400 | "时间字段必须为 ISO 8601 格式" |
| 超过截止时间 | `BIZ_001` | 400 | "日报提交已超过截止时间" |
| 时区解析失败 | `SYS_002` | 500 | "无效的时区标识符" |

### 测试用例 (Test Intent)

**TC-DATA-002-01: 创建记录时自动记录UTC时间**
- **Given**: 用户在北京时间 2025-11-20 18:30:00 创建日报
- **When**: 后端接收请求并创建记录
- **Then**:
  - `daily_reports.created_at` 存储为 `2025-11-20 10:30:00+00` (UTC)
  - API响应返回 `"created_at": "2025-11-20T10:30:00Z"`

**TC-DATA-002-02: 前端显示本地时区**
- **Given**: 后端返回 `"created_at": "2025-11-20T10:30:00Z"`
- **When**: 前端渲染时间
- **Then**:
  - 用户在上海: 显示 `2025-11-20 18:30:00`
  - 用户在纽约: 显示 `2025-11-20 05:30:00`
  - 用户在伦敦: 显示 `2025-11-20 10:30:00`

**TC-DATA-002-03: 日报截止时间检查 (项目时区)**
- **Given**:
  - 项目 #101 时区为 `Asia/Shanghai`
  - 日报日期为 `2025-11-20`
  - 截止时间为 `2025-11-20 23:59:59 CST` (= `2025-11-20 15:59:59 UTC`)
- **When**: 用户在 `2025-11-20 16:00:00 UTC` 提交日报
- **Then**: 返回 HTTP 400, 错误码 `BIZ_001`, 消息 "日报提交已超过截止时间 (2025-11-20 23:59:59 Asia/Shanghai)"

**TC-DATA-002-04: 充值审批时效计算 (UTC时间戳)**
- **Given**:
  - 充值申请 R1 提交时间: `2025-11-20 10:00:00Z`
  - 审批时效: 72小时
- **When**: 系统检查是否超期
- **Then**:
  - `2025-11-20 11:00:00Z` → 未超期
  - `2025-11-23 10:00:01Z` → 已超期 (超过72小时)

**TC-DATA-002-05: API响应格式验证**
- **Given**: 日报 ID=12345
- **When**: 调用 `GET /api/v1/daily-reports/12345`
- **Then**: 响应包含:
  ```json
  {
    "data": {
      "report_date": "2025-11-20",  // DATE格式
      "created_at": "2025-11-20T10:30:00Z",  // ISO 8601 UTC
      "submitted_at": "2025-11-20T11:45:00Z"
    },
    "timestamp": "2025-11-20T12:00:00Z"  // 响应时间戳
  }
  ```

**TC-DATA-002-06: 对账周期计算 (项目时区)**
- **Given**: 项目 #102 时区为 `America/New_York`, 对账月份为 `2025-11`
- **When**: 生成对账批次
- **Then**:
  - 开始时间: `2025-11-01 00:00:00 EST` (= `2025-11-01 05:00:00 UTC`)
  - 结束时间: `2025-11-30 23:59:59 EST` (= `2025-12-01 04:59:59 UTC`)

---

## 附录

### A. 相关文档

- `DATA_SCHEMA.md` - 数据结构定义
- `ERROR_CODES.md` - 错误码清单
- `STATE_MACHINE.md` - 状态机定义
- `AI_AD_SYSTEM_MASTER_SPEC_v2.2.md` - 核心开发手册

### B. 时区处理工具库

**Python**:
- `pytz` - 时区转换
- `python-dateutil` - 日期解析

**TypeScript**:
- `date-fns` - 日期格式化
- `date-fns-tz` - 时区转换

### C. 变更历史

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|---------|------|
| v1.0 | 2025-11-20 | 初始版本,包含 BR-DATA-001~002 | 系统架构团队 |

---

**END OF DOCUMENT**
