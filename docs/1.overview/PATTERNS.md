# PATTERNS.md - AI 广告代投系统反模式清单

> **文档性质**: 实现层禁止模式与危害说明
> **约束级别**: 项目级，所有代码实现必须避免本文档列出的反模式
> **版本**: v1.0
> **基准**: MASTER.md v3.4, ARCHITECTURE.md v1.0, DOMAIN.md v1.0

---

## 第一章 文档定位与使用

### 1.1 本文档职责

PATTERNS.md 定义实现层的"黑名单"：

- 列出禁止的编码模式
- 说明每种反模式的危害
- 提供引用依据（指向 MASTER/SoT）
- 作为 Code Review 的检查清单

### 1.2 本文档不做

本文档不承担以下职责：

- 不提供最佳实践教程（属于开发指南）
- 不定义业务规则（属于 BUSINESS_RULES.md）
- 不定义数据结构（属于 DATA_SCHEMA.md）
- 不重复 SoT 内容（仅引用）

### 1.3 使用方式

| 场景 | 动作 |
|-----|------|
| Code Review | 对照反模式清单逐项检查 |
| PR 检查 | 命中任一 P0 反模式必须拒绝 |
| 新人培训 | 了解"不能做什么" |
| AI 生成代码 | 验证是否命中反模式 |

### 1.4 危害等级定义

| 等级 | 说明 | 处理方式 |
|-----|------|---------|
| P0 | 违反系统不可变量 | PR 立即拒绝 |
| P1 | 违反架构约束 | 必须修复后合并 |
| P2 | 违反编码规范 | 建议修复 |

---

## 第二章 领域模型反模式

### AP-DM-001 在非 Domain 层定义业务规则

**危害等级**: P1

**描述**: 在 Controller、Router 或 Repository 层编写业务判断逻辑。

**危害**:
- 破坏四层架构的职责划分
- 业务逻辑散落，难以维护和测试
- 修改业务规则需要搜索多处代码

**检测方式**:
```python
# 错误示例：在 Router 中判断业务逻辑
@router.post("/daily-reports")
async def create_report(data: ReportCreate):
    if data.conversions_final > 1000:  # 业务规则不应在此
        raise HTTPException(...)
```

> 引用: ARCHITECTURE.md §2.3 层职责定义

---

### AP-DM-002 跨领域直接访问聚合根内部

**危害等级**: P1

**描述**: 一个领域的 Service 直接访问另一个领域聚合根的内部属性。

**危害**:
- 破坏聚合边界，导致隐式耦合
- 数据一致性难以保证
- 领域边界模糊化

**检测方式**:
```python
# 错误示例：日报 Service 直接访问账本内部
class DailyReportService:
    def process(self):
        ledger = self.ledger_repo.get(id)
        ledger._internal_balance = 100  # 直接修改内部状态
```

> 引用: DOMAIN.md §6 跨域依赖约束

---

### AP-DM-003 在 Controller/Router 层编写业务判断

**危害等级**: P1

**描述**: 在 Presentation 层实现业务校验或状态判断。

**危害**:
- 违反职责分离原则
- Presentation 层应只负责请求解析和响应格式化
- 业务逻辑无法复用

**检测方式**:
```python
# 错误示例：Router 中判断状态
@router.patch("/reports/{id}")
async def update_report(id: int, data: dict):
    report = get_report(id)
    if report.status == "final_locked":  # 不应在此判断
        raise HTTPException(400, "Cannot modify")
```

> 引用: ARCHITECTURE.md §2.3「Presentation 层禁止业务逻辑」

---

### AP-DM-004 创建未在 DOMAIN.md 索引的新实体

**危害等级**: P2

**描述**: 在代码中创建新的领域实体，但未在 DOMAIN.md 中注册。

**危害**:
- 实体定义漂移，无法追溯
- 破坏 SoT 体系完整性
- 新成员无法找到实体归属

**检测方式**: 新增 Model 类时检查 DOMAIN.md §4 是否已索引。

> 引用: DOMAIN.md §4 领域实体清单

---

## 第三章 账务与账本反模式

### AP-LED-001 直接 UPDATE/DELETE ledger_entries 记录

**危害等级**: P0

**描述**: 对已存在的 ledger_entries 记录执行 UPDATE 或 DELETE 操作。

**危害**:
- 破坏审计链，历史记录不可追溯
- 违反「账务只追加，不修改」不可变量
- 审计合规风险

**检测方式**:
```sql
-- 禁止的操作
UPDATE ledger_entries SET amount = 100 WHERE id = 1;
DELETE FROM ledger_entries WHERE id = 1;
```

> 引用: MASTER.md INV-001「禁止 UPDATE/DELETE 任何 ledger_entries 记录」

---

### AP-LED-002 直接修改 balance 字段而不写 ledger_entry

**危害等级**: P0

**描述**: 直接更新 projects.balance 或 suppliers.balance 字段。

**危害**:
- 余额与账本记录不一致
- 审计链断裂，无法追溯余额变化来源
- 违反「余额 = SUM(entries)」不变量

**检测方式**:
```python
# 错误示例
project.balance = project.balance + 100  # 直接修改
db.commit()
```

> 引用: MASTER.md INV-001「balance = SUM(ledger_entries.amount)」

---

### AP-LED-003 绕过日报直接写入账本记录

**危害等级**: P0

**描述**: 不通过日报流程，直接向 ledger_entries 插入 REVENUE 或 COST 记录。

**危害**:
- 违反「账务必须源于日报」不可变量
- 数据来源不可追溯
- 收入/成本数据与投放数据脱节

**检测方式**:
```python
# 错误示例：直接插入账本
ledger_entry = LedgerEntry(
    type="REVENUE",
    daily_report_id=None,  # 无日报关联
    amount=1000
)
```

> 引用: MASTER.md BI-04, PROJECT.md D-02「跳过日报直入账本」

---

### AP-LED-004 在 PROJECT 账本记录 COST 类型

**危害等级**: P0

**描述**: 向 category='PROJECT' 的账本插入 type='COST' 的记录。

**危害**:
- 违反双账本隔离约束
- 收入与成本混记，无法独立核算
- 对账困难

**检测方式**:
```python
# 错误示例
LedgerEntry(category="PROJECT", type="COST", ...)  # 非法组合
```

> 引用: MASTER.md INV-001「禁止在 PROJECT 账本记录 COST 类型」

---

### AP-LED-005 在 SUPPLIER 账本记录 REVENUE 类型

**危害等级**: P0

**描述**: 向 category='SUPPLIER' 的账本插入 type='REVENUE' 的记录。

**危害**:
- 违反双账本隔离约束
- 收入与成本混记
- 对账困难

**检测方式**:
```python
# 错误示例
LedgerEntry(category="SUPPLIER", type="REVENUE", ...)  # 非法组合
```

> 引用: MASTER.md INV-001「禁止在 SUPPLIER 账本记录 REVENUE 类型」

---

### AP-LED-006 红冲时修改原记录而非追加 REVERSAL

**危害等级**: P0

**描述**: 执行红冲修正时，直接修改原 ledger_entry 记录。

**危害**:
- 破坏账务不可变性
- 历史记录被篡改
- 违反红冲机制

**检测方式**:
```python
# 错误示例：修改原记录
original_entry.amount = 0  # 禁止
original_entry.is_reversed = True
db.commit()

# 正确做法：追加 REVERSAL 记录
reversal_entry = LedgerEntry(type="REVERSAL", ...)
```

> 引用: MASTER.md INV-003「红冲机制」, LEDGER_SOT.md §3

---

## 第四章 状态机反模式

### AP-SM-001 绕过状态机直接修改 status 字段

**危害等级**: P0

**描述**: 不通过状态机服务，直接 UPDATE 实体的 status 字段。

**危害**:
- 状态流转失控，可能跳入非法状态
- 绕过状态变更的校验逻辑
- 审计日志缺失

**检测方式**:
```python
# 错误示例
report.status = "final_locked"  # 直接赋值
db.commit()
```

> 引用: MASTER.md INV-003「禁止绕过状态机直接修改」

---

### AP-SM-002 在代码中自定义状态枚举

**危害等级**: P1

**描述**: 在代码中定义新的状态值，而不是引用 STATE_MACHINE.md。

**危害**:
- 状态定义漂移，与 SoT 不一致
- 代码与文档脱节
- 前后端状态理解不一致

**检测方式**:
```python
# 错误示例：自定义状态
class ReportStatus(Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"  # STATE_MACHINE.md 中无此状态
    APPROVED = "approved"    # 也无此状态
```

> 引用: STATE_MACHINE.md §8, CLAUDE.md「禁止重复定义状态枚举」

---

### AP-SM-003 实现终态回退

**危害等级**: P0

**描述**: 将 final_locked 状态的数据回退到之前的状态。

**危害**:
- 违反「终态不可逆」原则
- 已计费/计成本的数据被篡改
- 审计链断裂

**检测方式**:
```python
# 错误示例
if report.status == "final_locked":
    report.status = "final_confirmed"  # 终态回退，禁止
```

> 引用: MASTER.md INV-003「终态 final_locked 后数据冻结」

---

### AP-SM-004 跳过中间状态直接流转

**危害等级**: P1

**描述**: 状态流转时跳过必经的中间状态。

**危害**:
- 绕过风控/审批环节
- 业务流程失控
- 数据未经必要校验

**检测方式**:
```python
# 错误示例：跳过 trend_pending 直接到 final_pending
if report.status == "raw_submitted":
    report.status = "final_pending"  # 跳过中间状态
```

> 引用: STATE_MACHINE.md §8 状态流转白名单

---

### AP-SM-005 在非 Domain 层执行状态流转

**危害等级**: P1

**描述**: 在 Controller、Router 或 Repository 层执行状态变更。

**危害**:
- 状态逻辑散落
- 无法统一校验流转合法性
- 难以维护

**检测方式**:
```python
# 错误示例：在 Router 中流转状态
@router.patch("/reports/{id}/confirm")
async def confirm_report(id: int):
    report = get_report(id)
    report.status = "final_confirmed"  # 应在 Domain Service 中
```

> 引用: ARCHITECTURE.md §2.3「Domain 层: 状态机」

---

## 第五章 API 与 Service 反模式

### AP-API-001 使用未定义的错误码

**危害等级**: P1

**描述**: 在 Service 中返回 ERROR_CODES_SOT.md 未定义的错误码。

**危害**:
- 错误码漂移，前端无法统一处理
- 违反 SoT 唯一性原则
- 国际化/文档维护困难

**检测方式**:
```python
# 错误示例：自创错误码
raise BusinessError(code="MY_CUSTOM_ERROR", ...)  # 未在 SoT 定义
```

> 引用: ERROR_CODES_SOT.md, CLAUDE.md「禁止自定义错误码」

---

### AP-API-002 API 响应结构与 API_SOT 不一致

**危害等级**: P1

**描述**: API 实际返回的数据结构与 API_SOT.md 定义不一致。

**危害**:
- 前后端契约断裂
- 集成测试失败
- 文档不可信

**检测方式**: 比对 API 响应与 API_SOT.md 中的 Schema 定义。

> 引用: API_SOT.md v2.2

---

### AP-API-003 在单个 API 中混合 raw/real/final 数据

**危害等级**: P1

**描述**: 单个 API 的输入或输出同时包含 raw、real、final 三种数据流。

**危害**:
- 违反三数据流分离原则
- 数据语义混乱
- 前端处理复杂化

**检测方式**:
```python
# 错误示例：响应混合三种数据
return {
    "conversions_raw": 100,
    "conversions_real": 95,
    "conversions_final": 90,  # 三者不应同时出现在同一响应
}
```

> 引用: MASTER.md INV-002「三数据流分离」

---

### AP-API-004 Service 方法抛出未包装的原生异常

**危害等级**: P2

**描述**: Service 直接抛出 ValueError、KeyError 等原生异常。

**危害**:
- 异常泄露实现细节
- 错误处理不统一
- 前端无法根据错误码处理

**检测方式**:
```python
# 错误示例
def process_report(self, data):
    if not data:
        raise ValueError("Data is required")  # 应使用业务异常
```

> 引用: ARCHITECTURE.md §4.3「Result 模式错误处理」

---

### AP-API-005 在 Repository 层编写业务校验逻辑

**危害等级**: P1

**描述**: Repository 中包含业务规则判断。

**危害**:
- 职责混乱
- Repository 应只负责数据持久化
- 业务逻辑难以测试

**检测方式**:
```python
# 错误示例
class ReportRepository:
    def save(self, report):
        if report.conversions_final < 0:  # 业务校验不应在此
            raise ValueError("Invalid conversions")
```

> 引用: ARCHITECTURE.md §2.3「Infrastructure 层禁止业务规则」

---

## 第六章 数据访问与事务反模式

### AP-DA-001 使用原生 SQL 绕过 ORM

**危害等级**: P1

**描述**: 直接执行原生 SQL 查询，绕过 SQLAlchemy ORM。

**危害**:
- 绕过 RLS 策略，数据安全风险
- SQL 注入风险
- 失去 ORM 的类型安全

**检测方式**:
```python
# 错误示例
db.execute("SELECT * FROM ledger_entries WHERE id = " + str(id))
```

> 引用: ARCHITECTURE.md §5.4「禁止直接 SQL 查询绕过 ORM」

---

### AP-DA-002 跨 Service 直接访问其他 Service 的 Repository

**危害等级**: P1

**描述**: 一个 Service 直接调用另一个 Service 的 Repository。

**危害**:
- 破坏服务边界
- 耦合过紧，难以独立测试
- 修改一个 Repository 影响多个 Service

**检测方式**:
```python
# 错误示例
class DailyReportService:
    def __init__(self):
        self.ledger_repo = LedgerRepository()  # 应通过 LedgerService
```

> 引用: ARCHITECTURE.md §3.3「Repository 只被 Service 调用」

---

### AP-DA-003 在事务外执行账本写入操作

**危害等级**: P0

**描述**: 账本写入操作未包装在数据库事务中。

**危害**:
- 数据不一致，部分成功/部分失败
- 双账本可能只写入一边
- 余额与账本记录不一致

**检测方式**:
```python
# 错误示例：无事务包装
ledger_repo.create(transfer_out)
# 此处如果失败，transfer_out 已写入
ledger_repo.create(transfer_in)
```

> 引用: LEDGER_SOT.md §5「事务边界」, TRANSFER_SOT.md §9

---

### AP-DA-004 长事务持有锁超过 10 秒

**危害等级**: P1

**描述**: 单个事务执行时间过长，持有数据库锁超过 10 秒。

**危害**:
- 性能瓶颈，其他请求被阻塞
- 死锁风险增加
- 数据库连接池耗尽

**检测方式**: 监控事务执行时间，设置 `statement_timeout`。

> 引用: TRANSFER_SOT.md §9.4「事务执行时间应控制在 <10 秒」

---

### AP-DA-005 SELECT FOR UPDATE 锁定顺序不一致

**危害等级**: P1

**描述**: 不同代码路径以不同顺序锁定相同资源。

**危害**:
- 死锁风险
- 并发问题难以排查
- 系统不稳定

**检测方式**:
```python
# 事务 A：先锁 source，后锁 target
lock(source_account)
lock(target_account)

# 事务 B：先锁 target，后锁 source（死锁风险）
lock(target_account)
lock(source_account)
```

> 引用: TRANSFER_SOT.md §6「并发控制」

---

## 第七章 权限与安全反模式

### AP-SEC-001 在代码中硬编码角色判断逻辑

**危害等级**: P1

**描述**: 在业务代码中硬编码角色名称进行判断。

**危害**:
- 权限逻辑散落，难以统一修改
- 与 AUTH_SPEC 定义不一致风险
- 新增角色需要修改多处代码

**检测方式**:
```python
# 错误示例
if user.role == "admin" or user.role == "finance":
    # 应使用 @require_role 或权限服务
```

> 引用: AUTH_SPEC.md §5

---

### AP-SEC-002 跳过 @require_role 装饰器直接访问

**危害等级**: P0

**描述**: API 端点未使用权限装饰器，或通过内部调用绕过权限检查。

**危害**:
- 绕过权限校验
- 越权访问风险
- 安全漏洞

**检测方式**:
```python
# 错误示例：无权限装饰器
@router.post("/ledger/adjust")
async def adjust_ledger(data: dict):  # 缺少 @require_role
    ...
```

> 引用: AUTH_SPEC.md §5, ARCHITECTURE.md §6.2「认证必须」

---

### AP-SEC-003 在日志中输出敏感信息

**危害等级**: P1

**描述**: 日志中记录密码、Token、密钥等敏感信息。

**危害**:
- 安全风险，敏感信息泄露
- 合规问题
- 攻击者可从日志获取凭证

**检测方式**:
```python
# 错误示例
logger.info(f"User login: {username}, password: {password}")
logger.debug(f"API Key: {api_key}")
```

> 引用: ARCHITECTURE.md §6.2「敏感数据加密」

---

### AP-SEC-004 允许发起人审批自己的请求

**危害等级**: P0

**描述**: 系统允许同一用户既发起又审批同一请求。

**危害**:
- 违反职责分离（SOD）原则
- 风控失效
- 审计合规问题

**检测方式**:
```python
# 错误示例：未检查发起人与审批人
def approve_transfer(transfer_id, approver_id):
    transfer = get_transfer(transfer_id)
    # 应检查 transfer.created_by != approver_id
    transfer.status = "approved"
```

> 引用: MASTER.md INV-004「职责分离」, TRANSFER_SOT.md §11.2

---

## 第八章 部署与回滚反模式

### AP-DEP-001 通过数据库回滚覆盖现有账务数据

**危害等级**: P0

**描述**: 使用数据库快照恢复覆盖已有的 ledger_entries 数据。

**危害**:
- 违反账务不可篡改原则
- 审计链断裂
- 已确认的账务记录丢失

**检测方式**: 审查恢复流程，确保不覆盖 ledger_entries 表。

> 引用: MASTER.md BI-01, DEPLOYMENT.md §5.3「禁止回滚 ledger_entries 数据」

---

### AP-DEP-002 Schema 迁移删除已有字段

**危害等级**: P1

**描述**: 数据库迁移脚本中包含 DROP COLUMN 操作。

**危害**:
- 数据丢失，不可恢复
- 向后兼容性破坏
- 旧版本代码无法运行

**检测方式**:
```sql
-- 禁止的操作
ALTER TABLE daily_reports DROP COLUMN conversions_raw;
```

> 引用: DEPLOYMENT.md §5.4「禁止删除字段」

---

### AP-DEP-003 回滚操作影响 final_locked 状态数据

**危害等级**: P0

**描述**: 部署回滚导致 final_locked 状态的数据被修改或丢失。

**危害**:
- 违反终态保护原则
- 已计费数据被篡改
- 审计合规风险

**检测方式**: 审查回滚脚本，确保不影响终态数据。

> 引用: MASTER.md INV-003, DEPLOYMENT.md §5.3

---

### AP-DEP-004 跳过 CI/CD 流程直接部署

**危害等级**: P1

**描述**: 绕过 CI/CD 流水线，直接在生产环境部署代码。

**危害**:
- 绕过质量门禁（Lint/Test/Build）
- 未经审核的代码上线
- 风险不可控

**检测方式**: 审查部署记录，确保所有部署通过 CI/CD。

> 引用: DEPLOYMENT.md §3「CI/CD 流程」

---

## 第九章 AI 与自动化反模式

### AP-AI-001 AI 生成代码未经人工 Review 直接合并

**危害等级**: P1

**描述**: AI 生成的代码未经人工审查直接合并到主分支。

**危害**:
- 可能引入违反 SoT 的逻辑
- AI 幻觉导致错误代码
- 安全风险

**检测方式**: PR 必须有人工审批记录。

> 引用: DEPLOYMENT.md §3.4「PR 审批要求」

---

### AP-AI-002 AI 自动补全 SoT 中未定义的字段/状态

**危害等级**: P1

**描述**: AI 在生成代码时"发明"了 SoT 中不存在的字段或状态。

**危害**:
- 信息幻觉，与规范不一致
- 代码与 SoT 脱节
- 集成失败

**检测方式**: 代码中的字段/状态必须能在 DATA_SCHEMA/STATE_MACHINE 中找到。

> 引用: CLAUDE.md「禁止发明 SoT 中不存在的字段」

---

### AP-AI-003 自动化脚本直接修改账本数据

**危害等级**: P0

**描述**: 定时任务或自动化脚本直接 UPDATE/DELETE ledger_entries。

**危害**:
- 绕过业务流程
- 审计链断裂
- 违反账务不可变性

**检测方式**: 审查所有自动化脚本，确保不直接修改账本。

> 引用: MASTER.md INV-001, PROJECT.md D-01

---

### AP-AI-004 使用 AI 推测的业务规则替代 SoT 定义

**危害等级**: P1

**描述**: 当 AI 不确定业务规则时，自行推测而非查阅 SoT。

**危害**:
- 规则漂移
- 违反「SoT 为唯一真相源」原则
- 实现与规范不一致

**检测方式**: AI 生成代码时必须引用具体 SoT 文档章节。

> 引用: CLAUDE.md「遇到未覆盖场景提出 RFC，而非自行扩展」

---

## 附录 A: 反模式索引表

| 编号 | 类别 | 危害等级 | 简述 | 引用依据 |
|------|------|---------|------|---------|
| AP-DM-001 | 领域模型 | P1 | 非 Domain 层定义业务规则 | ARCHITECTURE.md §2.3 |
| AP-DM-002 | 领域模型 | P1 | 跨领域访问聚合根内部 | DOMAIN.md §6 |
| AP-DM-003 | 领域模型 | P1 | Controller 编写业务判断 | ARCHITECTURE.md §2.3 |
| AP-DM-004 | 领域模型 | P2 | 创建未索引的新实体 | DOMAIN.md §4 |
| AP-LED-001 | 账务 | P0 | UPDATE/DELETE ledger_entries | MASTER.md INV-001 |
| AP-LED-002 | 账务 | P0 | 直接修改 balance 字段 | MASTER.md INV-001 |
| AP-LED-003 | 账务 | P0 | 绕过日报直接写账本 | MASTER.md BI-04 |
| AP-LED-004 | 账务 | P0 | PROJECT 账本记录 COST | MASTER.md INV-001 |
| AP-LED-005 | 账务 | P0 | SUPPLIER 账本记录 REVENUE | MASTER.md INV-001 |
| AP-LED-006 | 账务 | P0 | 红冲修改原记录 | MASTER.md INV-003 |
| AP-SM-001 | 状态机 | P0 | 绕过状态机修改 status | MASTER.md INV-003 |
| AP-SM-002 | 状态机 | P1 | 自定义状态枚举 | STATE_MACHINE.md |
| AP-SM-003 | 状态机 | P0 | 实现终态回退 | MASTER.md INV-003 |
| AP-SM-004 | 状态机 | P1 | 跳过中间状态 | STATE_MACHINE.md §8 |
| AP-SM-005 | 状态机 | P1 | 非 Domain 层执行状态流转 | ARCHITECTURE.md §2.3 |
| AP-API-001 | API/Service | P1 | 使用未定义错误码 | ERROR_CODES_SOT.md |
| AP-API-002 | API/Service | P1 | 响应结构与 API_SOT 不一致 | API_SOT.md |
| AP-API-003 | API/Service | P1 | 混合 raw/real/final 数据 | MASTER.md INV-002 |
| AP-API-004 | API/Service | P2 | 抛出未包装原生异常 | ARCHITECTURE.md §4.3 |
| AP-API-005 | API/Service | P1 | Repository 编写业务校验 | ARCHITECTURE.md §2.3 |
| AP-DA-001 | 数据访问 | P1 | 原生 SQL 绕过 ORM | ARCHITECTURE.md §5.4 |
| AP-DA-002 | 数据访问 | P1 | 跨 Service 访问 Repository | ARCHITECTURE.md §3.3 |
| AP-DA-003 | 数据访问 | P0 | 事务外执行账本写入 | LEDGER_SOT.md §5 |
| AP-DA-004 | 数据访问 | P1 | 长事务超过 10 秒 | TRANSFER_SOT.md §9.4 |
| AP-DA-005 | 数据访问 | P1 | 锁定顺序不一致 | TRANSFER_SOT.md §6 |
| AP-SEC-001 | 权限安全 | P1 | 硬编码角色判断 | AUTH_SPEC.md §5 |
| AP-SEC-002 | 权限安全 | P0 | 跳过权限装饰器 | AUTH_SPEC.md §5 |
| AP-SEC-003 | 权限安全 | P1 | 日志输出敏感信息 | ARCHITECTURE.md §6.2 |
| AP-SEC-004 | 权限安全 | P0 | 发起人审批自己 | MASTER.md INV-004 |
| AP-DEP-001 | 部署回滚 | P0 | 回滚覆盖账务数据 | MASTER.md BI-01 |
| AP-DEP-002 | 部署回滚 | P1 | Schema 删除已有字段 | DEPLOYMENT.md §5.4 |
| AP-DEP-003 | 部署回滚 | P0 | 回滚影响终态数据 | MASTER.md INV-003 |
| AP-DEP-004 | 部署回滚 | P1 | 跳过 CI/CD 直接部署 | DEPLOYMENT.md §3 |
| AP-AI-001 | AI 自动化 | P1 | AI 代码未经 Review | DEPLOYMENT.md §3.4 |
| AP-AI-002 | AI 自动化 | P1 | AI 补全未定义字段 | CLAUDE.md |
| AP-AI-003 | AI 自动化 | P0 | 自动化修改账本 | MASTER.md INV-001 |
| AP-AI-004 | AI 自动化 | P1 | AI 推测替代 SoT | CLAUDE.md |

---

## 附录 B: 变更记录

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|---------|------|
| v1.0 | 2025-11-25 | 初始版本 | AI Doc Orchestrator |

---

**文档版本**: v1.0
**最后更新**: 2025-11-25
**对齐文档**: MASTER.md v3.4, ARCHITECTURE.md v1.0, DOMAIN.md v1.0
**维护者**: Tech Lead
