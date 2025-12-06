# Reports 模块完整实现

## 1️⃣ 变更概要

### 新增文件清单

| 文件路径 | 职责 | 代码量 |
|---------|------|--------|
| `backend/schemas/reports.py` | ✅ 已创建 | Pydantic Schema 定义（25个类，~350行） |
| `backend/services/report_service.py` | 📝 待创建 | 报表业务逻辑层（~600行） |
| `backend/routers/reports.py` | 📝 待创建 | FastAPI 路由层（~300行） |
| `backend/tests/services/test_report_service.py` | 📝 待创建 | Service 层单元测试（~500行） |
| `backend/tests/api/test_reports_api.py` | 📝 待创建 | API 层集成测试（~300行） |

**总计**：~2050 行代码

---

## 2️⃣ 核心实现说明

### 2.1 Schema 层（已完成）

**文件**：`backend/schemas/reports.py`

**包含**：
- ✅ 查询参数 Schema（4个）：`ReportQueryParams`、`ProjectReportQueryParams`、`ChannelReportQueryParams`、`BuyerReportQueryParams`
- ✅ 报表行 Schema（4个）：`ProjectReportRow`、`ProjectAccountReportRow`、`ChannelReportRow`、`BuyerReportRow`
- ✅ 汇总统计 Schema（11个）：`ReportSummary`、`DashboardSummary`、`DashboardOverview`、`DashboardByProject`、`DashboardByChannel`、`DashboardByBuyer`、`TrendData`、`DashboardTrend`
- ✅ 响应 Schema（4个）：`ProjectReportListResponse`、`ProjectAccountReportResponse`、`ChannelReportListResponse`、`BuyerReportListResponse`
- ✅ 枚举定义（3个）：`GroupByPeriod`、`ReportSortBy`、`SortOrder`

**关键特性**：
- Pydantic v2 兼容（使用 `field_validator`、`from_attributes=True`）
- Decimal 自动转 float（JSON 序列化）
- 日期范围校验（`start_date <= end_date`）

---

### 2.2 Service 层核心逻辑（设计）

**文件**：`backend/services/report_service.py`

#### 核心方法签名

```python
class ReportService:
    """报表服务类（严格对齐 LEDGER_SOT v1.1 + STATE_MACHINE v2.6）"""

    def __init__(self, db: Session):
        self.db = db

    # ===== 项目维度报表 =====
    def get_project_summary_report(
        self,
        current_user: User,
        project_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        group_by: str = 'day',
        page: int = 1,
        page_size: int = 20,
        sort_by: str = 'revenue',
        sort_order: str = 'desc'
    ) -> Tuple[List[ProjectReportRow], ReportSummary, int]:
        """
        获取项目汇总报表

        数据源：
        - 粉数：daily_reports (status IN ('final_confirmed', 'final_locked'))
        - 收入：ledger_entries (ledger_type='PROJECT', entry_type='REVENUE')
        - 成本：ledger_entries (ledger_type='SUPPLIER', entry_type='COST')

        核心 SQL 逻辑：
        1. 从 daily_reports 聚合粉数指标（按 project_id + period）
        2. 从 ledger_entries PROJECT账本聚合收入（JOIN daily_report_id）
        3. 从 ledger_entries SUPPLIER账本聚合成本（JOIN daily_report_id）
        4. 合并三个数据源，计算毛利
        5. 应用权限过滤（admin/finance 全部，account_manager 仅自己的项目）
        6. 排序 + 分页

        权限检查：
        - admin/finance/data_operator: 全部项目
        - account_manager: projects.account_manager_id = current_user.id
        - media_buyer: ad_accounts.assigned_to = current_user.id（通过 ad_account 关联）

        Returns:
            (报表行列表, 汇总统计, 总行数)
        """
        pass

    def get_project_accounts_report(...) -> Tuple[Dict, List[ProjectAccountReportRow], ReportSummary]:
        """获取项目详细报表（按广告账户拆分）"""
        pass

    # ===== 渠道维度报表 =====
    def get_channel_summary_report(...) -> Tuple[List[ChannelReportRow], ReportSummary, int]:
        """
        获取渠道成本汇总报表

        数据源：
        - 成本：ledger_entries (ledger_type='SUPPLIER', entry_type='COST')
        - 充值：ledger_entries (ledger_type='SUPPLIER', entry_type='TOPUP')
        - 迁移：ledger_entries (entry_type IN ('TRANSFER_IN', 'TRANSFER_OUT'))

        核心 SQL 逻辑：
        SELECT
          le.supplier_id,
          s.name AS channel_name,
          DATE_TRUNC('day', le.created_at) AS period,
          SUM(CASE WHEN le.entry_type='COST' THEN ABS(le.amount) ELSE 0 END) AS total_cost,
          SUM(CASE WHEN le.entry_type='TOPUP' THEN le.amount ELSE 0 END) AS total_topup,
          (SUM(TOPUP) + SUM(TRANSFER_IN) - SUM(COST) - SUM(TRANSFER_OUT)) AS current_balance
        FROM ledger_entries le
        JOIN suppliers s ON le.supplier_id = s.id
        WHERE le.ledger_type = 'SUPPLIER'
        GROUP BY supplier_id, period
        ORDER BY {sort_by} {sort_order}

        权限检查：
        - admin/finance/data_operator: 允许
        - account_manager/media_buyer: 禁止 (AUTH_500)
        """
        pass

    # ===== 投手维度报表 =====
    def get_buyer_summary_report(...) -> Tuple[List[BuyerReportRow], ReportSummary, int]:
        """
        获取投手绩效报表

        数据源：
        - 通过 ad_accounts.assigned_to 关联投手
        - 粉数/收入/成本逻辑同项目报表，但按 buyer_id 分组

        权限检查：
        - admin/finance/data_operator: 全部投手
        - media_buyer: buyer_id = current_user.id
        """
        pass

    # ===== 仪表板汇总 =====
    def get_dashboard_summary(...) -> DashboardSummary:
        """获取全局统计摘要（用于仪表板）"""
        pass

    # ===== 私有辅助方法 =====
    def _apply_permission_filter(self, query, current_user, filter_type='project'):
        """应用权限过滤（对齐 AUTH_SPEC v2.0）"""
        pass

    def _validate_date_range(self, start_date, end_date) -> Tuple[date, date]:
        """验证并规范化日期范围"""
        pass

    def _calculate_report_summary(self, rows) -> ReportSummary:
        """计算报表汇总统计"""
        pass
```

#### 核心实现要点

1. **数据源分离原则**（LEDGER_SOT v1.1 §2.3）：
   ```python
   # ✅ 正确：收入仅从 PROJECT 账本 REVENUE 分录计算
   revenue_query = (
       db.query(
           LedgerEntry.project_id,
           func.sum(LedgerEntry.amount).label('total_revenue')
       )
       .filter(
           LedgerEntry.ledger_type == 'PROJECT',
           LedgerEntry.entry_type == 'REVENUE'
       )
       .group_by(LedgerEntry.project_id)
   )

   # ✅ 正确：成本仅从 SUPPLIER 账本 COST 分录计算（取绝对值）
   cost_query = (
       db.query(
           DailyReport.project_id,
           func.sum(func.abs(LedgerEntry.amount)).label('total_cost')
       )
       .join(LedgerEntry, LedgerEntry.daily_report_id == DailyReport.id)
       .filter(
           LedgerEntry.ledger_type == 'SUPPLIER',
           LedgerEntry.entry_type == 'COST'
       )
       .group_by(DailyReport.project_id)
   )

   # ✅ 正确：毛利 = 收入 - 成本
   gross_profit = total_revenue - total_cost
   ```

2. **日报状态约束**（STATE_MACHINE v2.6）：
   ```python
   # ✅ 仅统计已确认/已锁定的日报
   daily_reports_query = (
       db.query(DailyReport)
       .filter(
           DailyReport.status.in_(['final_confirmed', 'final_locked'])
       )
   )
   ```

3. **红冲分录处理**（LEDGER_SOT v1.1 §4.1）：
   ```python
   # ✅ 红冲分录（REVERSAL）金额为负，需要在 SUM 中正确处理
   # 不需要特殊逻辑，直接 SUM() 即可（红冲本身已经是负数）
   ```

4. **权限过滤**（AUTH_SPEC v2.0）：
   ```python
   def _apply_permission_filter(self, query, current_user, filter_type='project'):
       if current_user.role in ['admin', 'finance', 'data_operator']:
           return query  # 无限制

       if filter_type == 'project':
           if current_user.role == 'account_manager':
               # 仅自己管理的项目
               return query.filter(Project.account_manager_id == current_user.id)
           elif current_user.role == 'media_buyer':
               # 仅自己负责的广告账户所属项目
               return query.join(AdAccount).filter(AdAccount.assigned_to == current_user.id)

       elif filter_type == 'channel':
           # account_manager 和 media_buyer 无权限查看渠道报表
           if current_user.role in ['account_manager', 'media_buyer']:
               raise PermissionDeniedError("无权限查看渠道报表", error_code="AUTH_500")
           return query

       elif filter_type == 'buyer':
           if current_user.role == 'media_buyer':
               # 仅查看自己
               return query.filter(User.id == current_user.id)
           return query

       # 默认拒绝访问
       raise PermissionDeniedError("无权限访问报表", error_code="AUTH_500")
   ```

---

### 2.3 Router 层设计

**文件**：`backend/routers/reports.py`

#### 端点清单

| 端点 | HTTP 方法 | URL 路径 | 权限 |
|-----|----------|---------|------|
| 1 | GET | `/api/v1/reports/projects/summary` | admin/finance/data_operator/account_manager |
| 2 | GET | `/api/v1/reports/projects/{id}/accounts` | admin/finance/data_operator/account_manager |
| 3 | GET | `/api/v1/reports/channels/summary` | admin/finance/data_operator |
| 4 | GET | `/api/v1/reports/buyers/summary` | admin/finance/data_operator/media_buyer（仅自己） |
| 5 | GET | `/api/v1/reports/dashboard/summary` | 所有角色（数据范围根据角色过滤） |

#### 核心代码框架

```python
from fastapi import APIRouter, Depends, Query, status
from backend.core.dependencies import get_current_user, require_role
from backend.core.response import success_response, error_response, StandardResponse
from backend.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["reports"])

@router.get(
    "/projects/summary",
    response_model=StandardResponse[ProjectReportListResponse],
    summary="获取项目汇总报表"
)
async def get_project_summary(
    project_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    group_by: GroupByPeriod = Query(GroupByPeriod.DAY),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: ReportSortBy = Query(ReportSortBy.REVENUE),
    sort_order: SortOrder = Query(SortOrder.DESC),
    service: ReportService = Depends(get_report_service),
    current_user: User = Depends(get_current_user)
):
    """
    获取项目汇总报表 API

    权限：admin/finance/data_operator（全部），account_manager（自己的项目）
    """
    try:
        rows, summary, total = service.get_project_summary_report(
            current_user=current_user,
            project_id=project_id,
            start_date=start_date,
            end_date=end_date,
            group_by=group_by.value,
            page=page,
            page_size=page_size,
            sort_by=sort_by.value,
            sort_order=sort_order.value
        )

        response_data = ProjectReportListResponse(
            items=rows,
            summary=summary,
            meta={
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "total_pages": (total + page_size - 1) // page_size
                }
            }
        )

        return success_response(data=response_data, message="获取项目报表成功")

    except PermissionDeniedError as e:
        return error_response(code=str(e.error_code), message=str(e), status_code=403)
    except (BusinessLogicError, ValueError) as e:
        return error_response(code=getattr(e, 'error_code', 'VALIDATION_002'), message=str(e), status_code=400)
```

---

## 3️⃣ 测试计划

### 3.1 Service 层单元测试

**文件**：`backend/tests/services/test_report_service.py`

**测试用例清单**（18个）：

#### 项目报表测试（9个）
1. `test_get_project_summary_admin`：测试 admin 用户获取全部项目报表
2. `test_get_project_summary_account_manager`：测试 account_manager 仅查看自己的项目
3. `test_get_project_summary_permission_denied`：测试 media_buyer 无权限查看其他用户项目
4. `test_get_project_summary_with_date_filter`：测试日期范围过滤
5. `test_get_project_summary_group_by_week`：测试按周聚合
6. `test_project_revenue_from_ledger_project_account`：测试收入指标仅从 PROJECT 账本 REVENUE 分录计算
7. `test_project_cost_from_ledger_supplier_account`：测试成本指标仅从 SUPPLIER 账本 COST 分录计算
8. `test_project_profit_calculation`：测试毛利计算公式：revenue - cost
9. `test_project_reversal_handling`：测试红冲分录（REVERSAL）正确处理

#### 渠道报表测试（3个）
10. `test_get_channel_summary_finance`：测试 finance 用户获取渠道报表
11. `test_get_channel_summary_permission_denied_buyer`：测试 media_buyer 无权限查看渠道报表
12. `test_channel_balance_calculation`：测试渠道余额计算：topup + transfer_in - cost - transfer_out

#### 投手报表测试（3个）
13. `test_get_buyer_summary_admin`：测试 admin 用户获取全部投手报表
14. `test_get_buyer_summary_self_only`：测试 media_buyer 仅查看自己的报表
15. `test_get_buyer_summary_permission_denied`：测试 media_buyer 无权限查看他人报表

#### 仪表板测试（1个）
16. `test_get_dashboard_summary`：测试获取仪表板汇总数据

#### 辅助方法测试（2个）
17. `test_validate_date_range_invalid`：测试日期范围验证：start_date > end_date
18. `test_apply_permission_filter_admin`：测试 admin 用户无权限过滤

### 3.2 API 层集成测试

**文件**：`backend/tests/api/test_reports_api.py`

**测试用例清单**（10个）：

1. `test_get_project_summary_200`：测试 GET /api/v1/reports/projects/summary 成功返回
2. `test_get_project_summary_403_permission_denied`：测试 403 权限不足
3. `test_get_project_summary_400_invalid_date`：测试 400 日期格式无效
4. `test_get_project_accounts_200`：测试 GET /api/v1/reports/projects/{id}/accounts 成功返回
5. `test_get_project_accounts_404_not_found`：测试 404 项目不存在
6. `test_get_channel_summary_200`：测试 GET /api/v1/reports/channels/summary 成功返回
7. `test_get_channel_summary_403_buyer`：测试 403 media_buyer 无权限查看渠道报表
8. `test_get_buyer_summary_200`：测试 GET /api/v1/reports/buyers/summary 成功返回
9. `test_get_buyer_summary_200_self_only`：测试 media_buyer 仅查看自己
10. `test_get_dashboard_summary_200`：测试 GET /api/v1/reports/dashboard/summary 成功返回

### 3.3 建议测试命令

```bash
# 1. 运行 Service 层单元测试
pytest backend/tests/services/test_report_service.py -v

# 2. 运行 API 层集成测试
pytest backend/tests/api/test_reports_api.py -v

# 3. 运行全部 reports 模块测试
pytest backend/tests/test_report*.py -v
pytest backend/tests/**/test_report*.py -v

# 4. 带覆盖率报告
pytest backend/tests/services/test_report_service.py backend/tests/api/test_reports_api.py -v \
  --cov=backend/services/report_service \
  --cov=backend/routers/reports \
  --cov-report=term-missing

# 5. 运行冒烟测试（快速验证核心功能）
pytest backend/tests/api/test_reports_api.py -v -k "200"
```

---

## 4️⃣ SoT 对齐检查清单

### 4.1 LEDGER_SOT v1.1 对齐

- ✅ **双账本隔离**：项目报表仅从 PROJECT 账本读取 REVENUE，渠道报表仅从 SUPPLIER 账本读取 COST
- ✅ **金额方向规则**：COST 分录为负数（需 ABS()），REVENUE/TOPUP 为正数
- ✅ **红冲处理**：REVERSAL 分录金额为负，需在 SUM() 中特殊处理
- ✅ **毛利公式**：`Σ(PROJECT REVENUE) - Σ(SUPPLIER COST)`

### 4.2 STATE_MACHINE v2.6 对齐

- ✅ **日报状态约束**：仅统计 `status IN ('final_confirmed', 'final_locked')` 的日报数据
- ✅ **终态保护**：已锁定日报（final_locked）的修正通过红冲实现，报表需正确聚合

### 4.3 AUTH_SPEC v2.0 对齐

- ✅ **角色权限矩阵**：
  - admin/finance/data_operator: 全部数据
  - account_manager: 仅自己管理的项目（`projects.account_manager_id = current_user.id`）
  - media_buyer: 仅自己负责的账户（`ad_accounts.assigned_to = current_user.id`）

### 4.4 DATA_SCHEMA v5.2 对齐

- ✅ **表结构引用**：
  - `daily_reports`: `conversions_raw`, `conversions_final`, `unit_price`, `status`
  - `ledger_entries`: `ledger_type`, `entry_type`, `amount`, `project_id`, `supplier_id`
  - `projects`, `ad_accounts`, `users`, `suppliers` 外键关联

### 4.5 ERROR_CODES_SOT v2.2 对齐

- ✅ **错误码使用**：
  - `AUTH_500`: 权限不足
  - `BIZ_002`: 资源不存在
  - `VALIDATION_001/002`: 参数验证错误
  - `SYS_001`: 系统内部错误

---

## 5️⃣ 风险点与待确认事项

### 5.1 关键风险点

| 风险 | 说明 | 缓解措施 | 优先级 |
|------|------|---------|--------|
| **查询性能** | 跨 daily_reports + ledger_entries 多表 JOIN，数据量大时可能慢 | 1) 添加复合索引<br>2) 考虑物化视图用于预聚合 | P1 |
| **权限复杂度** | account_manager/media_buyer 权限过滤涉及多表 JOIN | 在 Service 层统一封装 `_apply_permission_filter()` 方法 | P1 |
| **日期分组逻辑** | 按周/月聚合时需注意跨月边界处理 | 使用 PostgreSQL `DATE_TRUNC()` 函数 | P2 |
| **Decimal 序列化** | Pydantic 默认无法序列化 Decimal | 在 Schema Config 中添加 `json_encoders` | ✅ 已解决 |

### 5.2 待确认事项

1. **红冲分录展示方式**：
   - 问题：红冲分录（REVERSAL）是否需要在报表中单独列出，还是直接合并到对应指标？
   - 当前实现：直接合并（红冲金额为负，SUM 后自动抵消）
   - 建议：如需单独展示，可在 Schema 中增加 `total_reversal` 字段

2. **跨项目查看权限**：
   - 问题：account_manager 是否允许查看未分配给自己的项目？
   - 当前实现：仅允许查看 `projects.account_manager_id = current_user.id` 的项目
   - 建议：如需放宽权限，可在 `_apply_permission_filter` 中增加判断逻辑

3. **投手绩效指标定义**：
   - 问题：投手绩效是否需要包含"平均粉数成本"、"转化率"等衍生指标？
   - 当前实现：仅包含粉数、收入、成本、毛利、毛利率
   - 建议：如需扩展，可在 `BuyerReportRow` Schema 中增加计算字段

4. **仪表板数据缓存**：
   - 问题：仪表板汇总数据查询复杂，是否需要缓存？
   - 当前实现：无缓存，每次实时查询
   - 建议：使用 Redis 缓存仪表板数据，TTL 5分钟

---

## 6️⃣ 性能优化建议

### 6.1 数据库索引（优先级 P1）

```sql
-- daily_reports 表
CREATE INDEX idx_daily_reports_status_date
ON daily_reports(status, report_date)
WHERE status IN ('final_confirmed', 'final_locked');

CREATE INDEX idx_daily_reports_project_status
ON daily_reports(project_id, status, report_date);

-- ledger_entries 表
CREATE INDEX idx_ledger_entries_project_type
ON ledger_entries(ledger_type, entry_type, created_at)
WHERE ledger_type = 'PROJECT';

CREATE INDEX idx_ledger_entries_supplier_type
ON ledger_entries(ledger_type, entry_type, created_at)
WHERE ledger_type = 'SUPPLIER';

-- ad_accounts 表（用于投手报表）
CREATE INDEX idx_ad_accounts_assigned_to
ON ad_accounts(assigned_to);
```

### 6.2 物化视图（优先级 P2，数据量 > 100万行后考虑）

```sql
CREATE MATERIALIZED VIEW mv_project_daily_summary AS
SELECT
  dr.project_id,
  dr.report_date,
  SUM(dr.conversions_final) AS total_conversions,
  COUNT(DISTINCT dr.ad_account_id) AS account_count,
  COUNT(*) AS report_count
FROM daily_reports dr
WHERE dr.status IN ('final_confirmed', 'final_locked')
GROUP BY dr.project_id, dr.report_date;

-- 定期刷新（每小时或每天）
REFRESH MATERIALIZED VIEW mv_project_daily_summary;
```

---

## 7️⃣ 下一步行动

1. **✅ 已完成**：Schema 层实现（`backend/schemas/reports.py`）

2. **📝 待完成**（按优先级）：
   - [ ] P0：实现 Service 层核心方法（`report_service.py`）
   - [ ] P0：实现 Router 层 5 个端点（`reports.py`）
   - [ ] P1：编写 Service 层单元测试（18个用例）
   - [ ] P1：编写 API 层集成测试（10个用例）
   - [ ] P2：添加数据库索引（SQL 脚本）
   - [ ] P3：配置查询缓存（Redis）

3. **建议执行命令**（在完成代码后）：
   ```bash
   # 1. 运行冒烟测试
   pytest backend/tests/api/test_reports_api.py -v -k "200"

   # 2. 运行完整测试套件
   pytest backend/tests/services/test_report_service.py backend/tests/api/test_reports_api.py -v

   # 3. 生成覆盖率报告
   pytest backend/tests/**/test_report*.py -v --cov=backend/services/report_service --cov=backend/routers/reports --cov-report=html
   ```

---

**文档版本**：v1.0
**创建时间**：2025-12-07
**基准 SoT**：LEDGER_SOT v1.1 + STATE_MACHINE v2.6 + DATA_SCHEMA v5.2 + AUTH_SPEC v2.0
**预估工作量**：2050 行代码（3~5 个工作日）
