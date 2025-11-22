# 文档审计报告 (docs 自动体检)

- 项目根目录：`D:\git\1108\AI_ad_spend02`
- 扫描目录：`D:\git\1108\AI_ad_spend02\docs`
- 文档总数：44

## 一、未归类或可疑位置的文档
- ⚠️ 以下文件不在预期的 docs 子目录结构中（core/api/modules/dev/deploy/design/scripts/archive），需要人工决定：

  - `API_RULEBOOK.md`
  - `MODULE_DEVELOPMENT_TEMPLATE.md`
  - `cleanup_docs.py`
  - `delivery\README.md`
  - `deployment\DEPLOYMENT_GUIDE.md`
  - `deployment\MONITORING_OPS.md`
  - `deployment\SECURITY_CONFIG.md`
  - `development\COMPONENT_EXAMPLES.tsx`
  - `development\DEVELOPMENT_STANDARDS.md`
  - `development\RELEASE_NOTES_v2.3.md`
  - `rule\.project-rules.md`
  - `rule\AGENTS.md`
  - `rule\AI 模块开发流程规范 v2.0.md`
  - `rule\AI_MODULE_DEVELOPMENT_WORKFLOW.md`
  - `rule\INTERFACE_DESIGN_TEMPLATE.md`
  - `rule\INTERFACE_DEVELOPMENT_CHECKLIST.md`
  - `rule\INTERFACE_TESTING_GUIDELINES.md`
  - `rule\README.md`
  - `rule\UI_DESIGN_GUIDE.md`
  - `rule\UI_LIST_PAGE_TEMPLATE.md`

## 二、关键风险关键词扫描结果

### 旧角色命名（manager / data_clerk 等）
- 文件：`MODULE_DEVELOPMENT_TEMPLATE.md`
  - 示例：`# ❌ 错误：使用废弃角色 if current_user.role == "manager":      # manager已废弃     pass if current`
  - 示例：`violations = []      # 检查废弃角色     if "manager" in code and "account_manager" not in c`
  - 示例：`ode:         violations.append("使用了废弃角色'manager'")      if "data_clerk" in code:`
  - 示例：`er已废弃     pass if current_user.role == "data_clerk":   # data_clerk已废弃     pass  # ✅ 正确：使用`
  - 示例：`ons.append("使用了废弃角色'manager'")      if "data_clerk" in code:         violations.append("使用`
- 文件：`core\AI_AD_SYSTEM_MAIN_DOCUMENT.md`
  - 示例：`ia_buyer` - ❌ **废弃角色**：遇到 `data_clerk`、`manager`、`trader` 等立即报错纠正 - ✅ **权限装饰器**：必须使用 `@`
  - 示例：`时，**只能使用上述5个角色枚举** > - 遇到 `data_clerk`、`manager`、`trader` 等旧角色名，应视为错误并立即纠正 > - 角色名称区分大小`
  - 示例：`er身份登录 SET LOCAL app.current_user_id = 'manager-uuid'; SET LOCAL app.current_role = 'ac`
  - 示例：`OM projects WHERE account_manager_id = 'manager-uuid';  -- 预期结果：只返回该经理负责的项目 ```  **测试4:`
  - 示例：`anager`, `media_buyer` - ❌ **废弃角色**：遇到 `data_clerk`、`manager`、`trader` 等立即报错纠正 - ✅ **权限装饰器`
- 文件：`core\API_DEVELOPMENT_FLOW.md`
  - 示例：`# ❌ 违规：使用废弃角色 if current_user.role == "manager":  # 错误：应为 account_manager if current_u`
  - 示例：`hon # 错误信息 PermissionDeniedError: Role 'manager' is not authorized  # 解决方法 1. 检查角色名是否正确`
  - 示例：`not authorized  # 解决方法 1. 检查角色名是否正确 2. manager → account_manager 3. data_clerk → data_`
  - 示例：`ccount_manager if current_user.role == "data_clerk":  # 错误：应为 data_operator ```  ### 响应违规`
  - 示例：`角色名是否正确 2. manager → account_manager 3. data_clerk → data_operator ```  #### 错误3：前端调用失败 ```
- 文件：`core\DATA_SCHEMA.md`
  - 示例：`ame`: 用户姓名 - `role`: 角色名称，枚举值：`admin`, `manager`, `data_clerk`, `finance`, `media_buyer`
  - 示例：`--------| | `admin` | 系统管理员 | 全部权限 | | `manager` | 项目经理 | 管理自己的项目 | | `data_clerk` | 数据`
  - 示例：`查看所有         elif current_user.role == "manager":             return query.filter(Proje`
  - 示例：`return True         elif user.role == "manager":             return project.account_ma`
  - 示例：`atus_code=201) @require_role(["admin", "manager"])  # 接口级权限 async def create_project(`
- 文件：`core\SYSTEM_OVERVIEW.md`
  - 示例：`值初审、账户状态维护）。 - **account_manager**（历史称呼：manager）：账户/渠道/项目分配与日常运营协调（户管）。 - **media_buyer`
  - 示例：`ia_buyer**：广告投手，投放与日报提交，限被分配范围。  注：历史称呼 manager/data_clerk 已统一为 account_manager/data_op`
  - 示例：`结算报表，全量财务数据查看。 - **data_operator**（历史称呼：data_clerk）：数据录入/核验（日报审核、充值初审、账户状态维护）。 - **account`
  - 示例：`**：广告投手，投放与日报提交，限被分配范围。  注：历史称呼 manager/data_clerk 已统一为 account_manager/data_operator。实现与鉴`
- 文件：`deployment\SECURITY_CONFIG.md`
  - 示例：`current_setting('app.current_role') = 'data_clerk'         OR         -- 投手只能访问分配给自己的项目`
  - 示例：`current_setting('app.current_role') = 'data_clerk'         OR         -- 投手只能访问分配给自己的账户`
  - 示例：`current_setting('app.current_role') = 'data_clerk'         OR         -- 投手只能访问自己的日报`
  - 示例：`urrent_setting('app.current_role') IN ('data_clerk', 'finance')         OR         -- 投手只能`
- 文件：`rule\AI_MODULE_DEVELOPMENT_WORKFLOW.md`
  - 示例：`GET | /api/v1/{resource} | 获取列表 | admin,manager | 是 | 200 | | POST | /api/v1/{resource}`
  - 示例：`/api/v1/{resource}/{id} | 更新资源 | admin,manager | 是 | 200 | | PATCH | /api/v1/{resource`
  - 示例：`/api/v1/{resource}/{id} | 部分更新 | admin,manager | 否 | 200 | | DELETE | /api/v1/{resourc`
  - 示例：`encies=[Depends(require_role(["admin", "manager"]))] ) async def create_resource(     c`
- 文件：`rule\INTERFACE_DESIGN_TEMPLATE.md`
  - 示例：`限要求 - **角色权限**:   - ✅ admin - 管理员   - ✅ manager - 项目经理   - ✅ data_clerk - 数据员   - ❌ fin`
  - 示例：`admin - 管理员   - ✅ manager - 项目经理   - ✅ data_clerk - 数据员   - ❌ finance - 财务   - ❌ media_bu`
- 文件：`rule\INTERFACE_DEVELOPMENT_CHECKLIST.md`
  - 示例：`uter.post("/") @require_role(["admin", "manager"]) @require_permission("project:create"`

### 旧 Next.js 版本描述（13/15 等）
- 文件：`dev\FRONTEND_RULES.md`
  - 示例：``apiFetch` 统一处理 - 技术版本：Next.js 16；文档中任何 Next.js 13/15 的“现状”描述均无效 - 安全：CORS 使用白名单；不得使用 `*`（`
- 文件：`development\DEVELOPMENT_STANDARDS.md`
  - 示例：`## 2025-11-11  ### Query 1 - **目的**: 了解Next.js 15的新特性 - **查询**: resolve-library-id "next.`

### RLS 已启用 / 强依赖 RLS 的描述
- 文件：`core\AI_AD_SYSTEM_MAIN_DOCUMENT.md`
  - 示例：`**禁止RLS**：当前版本禁止启用 PostgreSQL RLS，不得执行 `ENABLE ROW LEVEL SECURITY`  ### 2. 角色权限硬规则  - ✅ **5个合法角色**：`admin`
  - 示例：`_user.id)`） > - ❌ 不要执行 `ALTER TABLE ... ENABLE ROW LEVEL SECURITY` > - ❌ 不要创建 PostgreSQL POLICY  ### 角色定义`
  - 示例：`执行！仅供未来参考 -- 启用RLS ALTER TABLE projects ENABLE ROW LEVEL SECURITY; ALTER TABLE ad_accounts ENABLE ROW LEV`
  - 示例：`LEVEL SECURITY; ALTER TABLE ad_accounts ENABLE ROW LEVEL SECURITY; ALTER TABLE daily_reports ENABLE ROW L`
  - 示例：`VEL SECURITY; ALTER TABLE daily_reports ENABLE ROW LEVEL SECURITY; ALTER TABLE topup_requests ENABLE ROW`
- 文件：`deployment\SECURITY_CONFIG.md`
  - 示例：`置  ```sql -- 启用RLS ALTER TABLE projects ENABLE ROW LEVEL SECURITY; ALTER TABLE ad_accounts ENABLE ROW LEV`
  - 示例：`LEVEL SECURITY; ALTER TABLE ad_accounts ENABLE ROW LEVEL SECURITY; ALTER TABLE daily_reports ENABLE ROW L`
  - 示例：`VEL SECURITY; ALTER TABLE daily_reports ENABLE ROW LEVEL SECURITY; ALTER TABLE recharge_requests ENABLE R`
  - 示例：`SECURITY; ALTER TABLE recharge_requests ENABLE ROW LEVEL SECURITY;  -- 创建RLS策略  -- 项目访问策略 CREATE POLICY p`
  - 示例：`` 为准。  ### 7.1 RLS策略配置  ```sql -- 启用RLS ALTER TABLE projects ENABLE ROW LEVEL SECURITY; ALTER TABLE ad_accounts ENABLE ROW LEV`
- 文件：`rule\.project-rules.md`
  - 示例：`板  ```sql -- 启用RLS ALTER TABLE projects ENABLE ROW LEVEL SECURITY;  -- 用户只能访问自己租户的数据 CREATE POLICY tenant`
  - 示例：`'; ```  ### 4. RLS策略模板  ```sql -- 启用RLS ALTER TABLE projects ENABLE ROW LEVEL SECURITY;  -- 用户只能访问自己租户的数据 CREATE POLICY tenant`

### 前端直接 fetch() 调用示例（可能绕过 apiFetch）
- 文件：`MODULE_DEVELOPMENT_TEMPLATE.md`
  - 示例：`// 1. 禁止直接fetch const response = await fetch('/api/v1/topups');  // ❌  // 2. 禁止使用axios imp`
  - 示例：`/ ❌ 错误：直接使用fetch const response = await fetch('/api/v1/topups', {   method: 'POST',   heade`
  - 示例：`弃角色'data_clerk'")      # 检查前端调用     if "fetch('/api/v1" in code:         violations.append(`
- 文件：`core\API_DEVELOPMENT_FLOW.md`
  - 示例：`禁止的方式 // 1. 禁止直接fetch const res = await fetch('/api/v1/topup-requests', {...});  // ❌  // 2`
  - 示例：`### 前端违规 ```typescript // ❌ 违规：直接fetch fetch('/api/v1/projects')  // ✅ 正确 apiClient.get('/`
- 文件：`deployment\SECURITY_CONFIG.md`
  - 示例：`st csrfToken = getCookie('csrf_token'); fetch('/api/projects', {   method: 'POST',   header`

### DATA_SCHEMA 路径错误引用（应为 docs/core/DATA_SCHEMA.md）
- 文件：`MODULE_DEVELOPMENT_TEMPLATE.md`
  - 示例：`格遵守以下规范：  ### 唯一真相源（不可覆盖） - **数据库结构**: `docs/core/DATA_SCHEMA.md` - 任何字段、表名、关系定义以此为准 - **系统规范**: `docs/c`
  - 示例：`#### topup_requests（充值申请表） ```sql -- 来源：docs/core/DATA_SCHEMA.md 第X行 CREATE TABLE topup_requests (     i`
  - 示例：`1. 确认表结构存在 grep -A 50 "topup_requests" docs/core/DATA_SCHEMA.md  # 2. 确认字段名正确 grep "finance_approved_at`
  - 示例：`# 2. 确认字段名正确 grep "finance_approved_at" docs/core/DATA_SCHEMA.md  # 3. 确认角色定义 grep "VALID_ROLES" docs/co`
  - 示例：`--  ## 🔗 相关文档  ### 必读文档（SoT） 1. [数据库结构](docs/core/DATA_SCHEMA.md) - **表结构唯一真相** 2. [系统规范](docs/core/AI_A`
- 文件：`core\AI_AD_SYSTEM_MAIN_DOCUMENT.md`
  - 示例：`数据库硬规则  - ✅ **唯一真相源**：任何数据库表/字段修改必须先查阅 `docs/core/DATA_SCHEMA.md` - ✅ **迁移管理**：只能通过 Alembic 创建数据库变更，禁止手动`
  - 示例：`⚠️ **重要声明：数据库结构权威来源** > > **本项目数据库结构以 `docs/core/DATA_SCHEMA.md` 和 Alembic 迁移文件为唯一权威来源**。本章中出现的 SQL 示例仅`
  - 示例：`帮助理解概念，**禁止直接作为实现依据**。实际开发时必须： > 1. 查阅 `docs/core/DATA_SCHEMA.md` 获取最新表结构定义 > 2. 使用 Alembic 管理数据库迁移（`ale`
  - 示例：`id |  > **AI 使用约束**：生成任何数据库相关代码时，必须先查阅 `docs/core/DATA_SCHEMA.md` 确认字段名称、类型和约束。禁止根据本章节的示例 SQL 创建表或添加字段。`
- 文件：`core\API_DEVELOPMENT_FLOW.md`
  - 示例：`--  ## ⚠️ 核心约束  ### 唯一真相源 - **数据库结构**: `docs/core/DATA_SCHEMA.md` - 任何字段、表名、关系定义以此为准 - **系统规范**: `docs/c`
  - 示例：`对齐（30分钟） ```yaml 输入: 需求确认单 动作:   1. 打开: docs/core/DATA_SCHEMA.md   2. 找到对应表定义   3. 复制准确的字段名和类型   4. 禁止:`
  - 示例：`# 1. 确认表结构 grep -A 50 "topup_requests" docs/core/DATA_SCHEMA.md  # 2. 确认角色权限 grep -A 10 "角色权限" docs/cor`
  - 示例：`e 'finance_approved_time'  # 解决方法 1. 打开 docs/core/DATA_SCHEMA.md 2. 搜索 topup_requests 表 3. 使用正确字段名：finan`
- 文件：`core\SQL_SCRIPTS_REVIEW.md`
  - 示例：`# SQL 脚本审查报告  > **审查依据**: `docs/core/DATA_SCHEMA.md`   > **审查日期**: 2025-01-XX   > **审查范围**:`

### 前端/文档中直接操作 Supabase 客户端的示例
- ✅ 未发现可疑内容。
