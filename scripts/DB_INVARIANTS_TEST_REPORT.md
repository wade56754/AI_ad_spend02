# 数据库不变量测试执行报告

> **执行日期**: 2025-11-25  
> **测试脚本**: `backend/db/db_invariants_test_v2.sql`  
> **测试用例文档**: `backend/db/TEST_CASES_v2.0.md`  
> **数据库**: Supabase (jzmcoivxhiyidizncyaq)

---

## 1. 测试概览

- **执行数据库**: Supabase 测试环境 (jzmcoivxhiyidizncyaq)
- **使用脚本**: `init_schema.sql` + `db_invariants_test_v2.sql`
- **总用例数**: 30
- **通过数**: 待完整执行后统计
- **失败数**: 待完整执行后统计
- **是否存在 P0 失败**: 待完整执行后确认

**当前状态**: 
- ✅ 数据库 schema 已初始化
- ✅ 测试辅助函数已创建
- ✅ 测试数据已准备
- ⚠️ 完整测试套件需要通过 Supabase Dashboard SQL Editor 执行（脚本包含 1216 行，包含大量 DO 块）

---

## 2. 测试用例清单

### P0 测试用例 (13个) - 核心不变量

#### 账本不可变性 (2个)
- TC-LED-001: 禁止 UPDATE ledger_entries
- TC-LED-002: 禁止 DELETE ledger_entries

#### 双账本隔离 (6个)
- TC-LED-003: PROJECT 账本必须关联 project_id
- TC-LED-004: PROJECT 账本禁止关联 supplier_id
- TC-LED-005: SUPPLIER 账本必须关联 supplier_id
- TC-LED-006: SUPPLIER 账本禁止关联 project_id
- TC-LED-007: PROJECT 账本只允许 REVENUE/TOPUP/REVERSAL
- TC-LED-008: SUPPLIER 账本只允许 COST/TOPUP/TRANSFER_*/REVERSAL

#### 供应商余额只读 (2个)
- TC-SUP-001: 禁止直接修改 suppliers.balance
- TC-SUP-002: 允许修改 suppliers 其他字段

#### 日报唯一约束与状态机 (3个)
- TC-RPT-001: daily_reports 日期+账户唯一约束
- TC-RPT-002: daily_reports 8 状态枚举约束
- TC-RPT-003: daily_reports 合法状态值验证

### P1 测试用例 (8个) - 枚举与流程

#### 用户角色枚举 (2个)
- TC-USR-001: users.role 5 角色枚举约束
- TC-USR-002: users.role 合法值验证

#### 充值状态枚举 (2个)
- TC-TOP-001: topup_requests.status 7 状态枚举约束
- TC-TOP-002: topup_requests.status 合法值验证

#### 广告账户状态枚举 (2个)
- TC-ACC-001: ad_accounts.status 6 状态枚举约束
- TC-ACC-002: ad_accounts.status 合法值验证

#### 死号迁移状态 (2个)
- TC-TRF-001: transfer_requests.status 5 状态枚举约束
- TC-TRF-002: transfer_requests.status 合法值验证

### P2 测试用例 (5个) - 视图与对账

#### 视图验证 (3个)
- TC-VW-001: v_project_balance 与 ledger_entries 聚合一致性
- TC-VW-002: v_project_balance 空项目返回 0
- TC-VW-003: v_supplier_balance 计算值验证

#### 对账模块 (2个)
- TC-REC-001: reconciliation_batches.status 5 状态枚举约束
- TC-REC-002: reconciliation_details.status 3 状态枚举约束

### 集成测试用例 (4个) - 端到端流程

- TC-FLOW-001: 完整充值流程
- TC-FLOW-002: 日报 8 状态流转
- TC-FLOW-003: 死号余额迁移流程
- TC-FLOW-004: 对账批次完整流程

---

## 3. 执行状态

### 已完成的步骤

1. ✅ **数据库初始化**: `init_schema.sql` 已成功执行
2. ✅ **测试辅助函数**: `test_assert` 和 `test_expect_exception` 已创建
3. ✅ **测试数据准备**: 测试用户、项目、供应商、渠道、广告账户已创建
4. ⚠️ **测试用例执行**: 部分测试用例已执行（TC-LED-001 已验证），但完整测试套件需要通过 Supabase Dashboard 执行

### 当前数据库状态

- 测试用户存在: ✅
- 测试项目存在: ✅
- 测试供应商存在: ✅
- 测试广告账户存在: ✅
- 测试账本记录: 1 条（来自 TC-LED-001）

---

## 4. 如何执行完整测试

### 方法 1: Supabase Dashboard SQL Editor（推荐）

1. 登录 Supabase Dashboard: https://supabase.com/dashboard
2. 选择项目: `AI_adspend` (jzmcoivxhiyidizncyaq)
3. 进入 **SQL Editor**
4. 复制 `backend/db/db_invariants_test_v2.sql` 的全部内容（1216 行）
5. 粘贴到 SQL Editor
6. 点击 **Run** 执行
7. 查看输出面板中的 `NOTICE` 消息：
   - `PASS: TC-XXX-YYY` 表示测试通过
   - `TEST_FAILED [TC-XXX-YYY]: ...` 表示测试失败

### 方法 2: psql 命令行

```bash
# 需要 Supabase 数据库连接信息
psql "postgresql://postgres:[PASSWORD]@db.jzmcoivxhiyidizncyaq.supabase.co:5432/postgres" \
  -f backend/db/db_invariants_test_v2.sql
```

---

## 5. 结果判读

### 成功输出示例

```
NOTICE:  ========================================
NOTICE:  开始准备测试数据...
NOTICE:  ========================================
NOTICE:  ----------------------------------------
NOTICE:  TC-LED-001: 禁止 UPDATE ledger_entries
NOTICE:  ----------------------------------------
NOTICE:  PASS: TC-LED-001 (expected exception matched: LEDGER_IMMUTABLE)
NOTICE:  ----------------------------------------
NOTICE:  TC-LED-002: 禁止 DELETE ledger_entries
NOTICE:  ----------------------------------------
NOTICE:  PASS: TC-LED-002 (expected exception matched: LEDGER_IMMUTABLE)
...
NOTICE:  ========================================
NOTICE:  所有测试执行完成 (v2.0)
NOTICE:  ========================================
NOTICE:  测试覆盖: P0 (13) + P1 (8) + P2 (5) + 集成 (4) = 30 用例
```

### 失败输出示例

```
ERROR:  TEST_FAILED [TC-XXX-YYY]: <失败原因>
```

---

## 6. 失败用例列表（待填写）

> **注意**: 执行完整测试后，请将失败用例填写到本节。

### P0 失败用例

（无 - 待执行后填写）

### P1 失败用例

（无 - 待执行后填写）

### P2 失败用例

（无 - 待执行后填写）

### 集成测试失败用例

（无 - 待执行后填写）

---

## 7. 结论建议

> **待完整测试执行后填写**

### 若全部通过

说明当前 schema 满足 DB 不变量要求，可作为上线前检查的一部分。

### 若有失败

- **P0 失败**: 阻断上线，必须修复
- **P1 失败**: 建议修复，但不阻断上线
- **P2 失败**: 可延后修复

**修复建议**:
- Schema 问题: 修改 `init_schema.sql` 并重新执行迁移
- 触发器问题: 检查触发器函数定义
- 业务逻辑问题: 检查相关业务代码

---

## 8. 测试脚本位置

- **测试脚本**: `backend/db/db_invariants_test_v2.sql`
- **测试用例文档**: `backend/db/TEST_CASES_v2.0.md`
- **数据库初始化脚本**: `backend/db/init_schema.sql`

---

**报告生成时间**: 2025-11-25  
**状态**: ⚠️ 部分执行 - 需要完整测试套件执行  
**下一步**: 在 Supabase Dashboard SQL Editor 中执行完整测试脚本
