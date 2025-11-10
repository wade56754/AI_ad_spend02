# AI广告代投系统开发文档

> **项目名称**: AI广告代投与财务管理系统
> **文档版本**: v1.0
> **创建日期**: 2025-11-10
> **文档类型**: 综合开发指南
> **适用角色**: 开发团队、项目管理、运维团队

---

## 📋 目录

1. [项目概述](#1-项目概述)
2. [技术架构](#2-技术架构)
3. [开发环境准备](#3-开发环境准备)
4. [业务流程实现详解](#4-业务流程实现详解)
5. [核心模块开发指南](#5-核心模块开发指南)
6. [数据模型与API设计](#6-数据模型与api设计)
7. [前端开发实现](#7-前端开发实现)
8. [部署与运维](#8-部署与运维)
9. [测试与质量保证](#9-测试与质量保证)
10. [常见问题与解决方案](#10-常见问题与解决方案)

---

## 1. 项目概述

### 1.1 项目背景

我们是一家专业的Facebook广告代投公司，为甲方客户提供广告投放服务。主要业务模式是通过收取项目启动费，并根据帮助甲方带来的潜在客户数量进行计费。

### 1.2 核心业务挑战

1. **投手效率管理**: 缺乏有效的绩效考核和实时监控
2. **财务对账困难**: 充值申请审批流程混乱，消耗与充值对账不清晰
3. **渠道管理复杂**: 多个广告代理商质量参差不齐，缺乏渠道绩效评估
4. **盈利分析不清晰**: 无法准确评估项目盈利状况
5. **账户生命周期管理**: 广告账户寿命不确定（几天到几个月不等）

### 1.3 系统目标

- **自动化流程**: 减少90%的人工数据录入工作
- **财务准确性**: 解决财务对账偏差问题，实现精准成本核算
- **决策支持**: 基于真实数据进行业务决策
- **扩展性**: 支持业务规模扩展和模式复制

### 1.4 核心业务流程

```mermaid
graph TD
    A[甲方签约付款] --> B[创建项目]
    B --> C[申请渠道账户]
    C --> D[分配账户给投手]
    D --> E[投手投放广告]
    E --> F[每日提交日报]
    F --> G[数据员审核甲方粉数]
    E --> H[提交充值申请]
    H --> I[数据员审核需求]
    I --> J[财务审批]
    J --> K[财务打款给代理商]
    K --> L[代理商充值]
    L --> M[月底财务对账]
    M --> N[项目盈利分析]
```

---

## 2. 技术架构

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    前端层 (Next.js)                         │
├─────────────────────────────────────────────────────────────┤
│                业务逻辑层 (FastAPI)                         │
├─────────────────────────────────────────────────────────────┤
│              数据访问层 (SQLAlchemy)                        │
├─────────────────────────────────────────────────────────────┤
│                数据层 (PostgreSQL)                          │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 技术栈

#### 前端技术栈
- **框架**: Next.js 14 (App Router)
- **语言**: TypeScript
- **样式**: Tailwind CSS + CSS Modules
- **UI组件**: Radix UI + 自定义组件
- **状态管理**: React Context + Hooks
- **图表库**: Recharts
- **认证**: Supabase Auth
- **API请求**: fetch + 自定义hook

#### 后端技术栈
- **框架**: FastAPI
- **语言**: Python 3.8+
- **数据库**: PostgreSQL + Supabase
- **ORM**: SQLAlchemy 2.0
- **认证**: JWT + Supabase Auth
- **数据验证**: Pydantic
- **API文档**: 自动生成OpenAPI/Swagger

#### 基础设施
- **数据库**: PostgreSQL (Supabase托管)
- **部署**: Vercel + 宝塔面板
- **监控**: 健康检查、审计日志
- **安全**: RLS行级安全、JWT加密

### 2.3 安全架构

- **数据安全**: RLS行级安全策略
- **认证授权**: JWT + 角色权限管理
- **操作审计**: 完整的操作日志记录
- **数据加密**: 敏感数据加密存储

---

## 3. 开发环境准备

### 3.1 系统要求

- **操作系统**: Windows 10/11, macOS, Ubuntu 20.04+
- **Python**: 3.8+
- **Node.js**: 18+
- **Git**: 2.30+

### 3.2 开发工具安装

```bash
# 1. 克隆项目
git clone <repository-url>
cd AI_ad_spend02

# 2. 后端环境配置
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. 前端环境配置
npm install

# 4. 环境变量配置
cp .env.example .env
# 编辑 .env 文件，填入实际配置
```

### 3.3 数据库设置

```bash
# 1. 创建Supabase项目
# 2. 获取数据库连接信息
# 3. 更新 .env 文件中的数据库配置
# 4. 运行数据库迁移
cd backend
python -m alembic upgrade head
```

### 3.4 启动开发服务器

```bash
# 启动后端服务
cd backend
python main.py

# 启动前端服务 (新终端)
cd app
npm run dev
```

### 3.5 验证环境

- 后端API: http://localhost:8000/docs
- 前端应用: http://localhost:3000
- 数据库连接: 检查日志输出

---

## 4. 业务流程实现详解

### 4.1 四层数据关系实现

#### 业务逻辑
```
项目 (Project) → 渠道 (Channel) → 广告账户 (AdAccount) → 投手 (User)
```

#### 数据模型设计

```python
# 项目模型 (projects.py)
class Project(Base):
    __tablename__ = "projects"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    client_name = Column(String(255), nullable=False)
    pricing_model = Column(String(50), default="per_lead")
    lead_price = Column(Numeric(10, 2), nullable=False)
    # ... 其他字段

# 渠道模型 (channels.py)
class Channel(Base):
    __tablename__ = "channels"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    service_fee_rate = Column(Numeric(5, 4), nullable=False)  # 5%-20%
    # ... 其他字段

# 广告账户模型 (ad_accounts.py)
class AdAccount(Base):
    __tablename__ = "ad_accounts"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    account_id = Column(String(255), unique=True, nullable=False)
    project_id = Column(GUID(), ForeignKey("projects.id"))
    channel_id = Column(GUID(), ForeignKey("channels.id"))
    assigned_user_id = Column(GUID(), ForeignKey("users.id"))
    status = Column(String(20), default="new")
    # ... 其他字段
```

#### 关键实现点

1. **外键约束**: 确保数据关系的完整性
2. **索引优化**: 在关联字段上建立索引
3. **级联删除**: 合理设置删除策略
4. **数据验证**: 在API层进行数据完整性验证

### 4.2 "粉"管理业务流程

#### 业务规则
1. **统一术语**: 潜在客户统一用"粉"指代
2. **数量确定**: 粉数最终由甲方反馈决定，不是系统自动统计
3. **数据来源**: 通过表单提交的潜在客户
4. **统计维度**: 只分项目和投手维度，不区分具体广告账户

#### 实现流程

```python
# 日报管理模型 (ad_spend_daily.py)
class AdSpendDaily(Base):
    __tablename__ = "ad_spend_daily"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    project_id = Column(GUID(), ForeignKey("projects.id"))
    user_id = Column(GUID(), ForeignKey("users.id"))  # 投手
    date = Column(Date, nullable=False)

    # 投手提交数据
    leads_submitted = Column(Integer, default=0)  # 投手统计的粉数
    spend = Column(Numeric(15, 2), nullable=False)

    # 甲方确认数据
    leads_confirmed = Column(Integer, nullable=True)  # 甲方确认的粉数
    confirmed_by = Column(GUID(), ForeignKey("users.id"))  # 数据员
    confirmed_at = Column(DateTime, nullable=True)

    # 差异分析
    leads_diff = Column(Integer, nullable=True)  # 差异数量
    diff_reason = Column(Text, nullable=True)  # 差异原因
```

#### API实现

```python
# routers/ad_spend.py
@router.post("/daily-report")
async def submit_daily_report(
    report: AdSpendDailyCreate,
    current_user: User = Depends(get_current_user)
):
    """投手提交日报"""
    # 验证用户权限
    if current_user.role != "media_buyer":
        raise HTTPException(403, "权限不足")

    # 创建日报记录
    daily_report = AdSpendDaily(
        project_id=report.project_id,
        user_id=current_user.id,
        date=report.date,
        leads_submitted=report.leads,
        spend=report.spend
    )

    db.add(daily_report)
    db.commit()

    # 通知数据员审核
    await notify_data_clerk(daily_report)

    return {"message": "日报提交成功", "id": daily_report.id}

@router.put("/daily-report/{report_id}/confirm")
async def confirm_daily_report(
    report_id: str,
    confirmation: AdSpendDailyConfirm,
    current_user: User = Depends(get_current_user)
):
    """数据员确认粉数"""
    # 验证权限
    if current_user.role not in ["data_clerk", "admin"]:
        raise HTTPException(403, "权限不足")

    # 获取日报记录
    report = db.query(AdSpendDaily).filter(
        AdSpendDaily.id == report_id
    ).first()

    if not report:
        raise HTTPException(404, "日报记录不存在")

    # 更新确认数据
    report.leads_confirmed = confirmation.leads_confirmed
    report.confirmed_by = current_user.id
    report.confirmed_at = datetime.utcnow()

    # 计算差异
    report.leads_diff = confirmation.leads_confirmed - report.leads_submitted
    if report.leads_diff != 0:
        report.diff_reason = confirmation.reason

    db.commit()

    return {"message": "粉数确认成功"}
```

### 4.3 简化充值流程实现

#### 业务流程
```
投手申请 → 数据员审核 → 财务审批 → 财务打款 → 代理商充值
```

#### 数据模型

```python
# topup.py
class Topup(Base):
    __tablename__ = "topups"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    project_id = Column(GUID(), ForeignKey("projects.id"))
    ad_account_id = Column(GUID(), ForeignKey("ad_accounts.id"))
    requested_by = Column(GUID(), ForeignKey("users.id"))  # 投手

    # 申请信息
    amount = Column(Numeric(15, 2), nullable=False)
    purpose = Column(Text, nullable=True)
    urgency_level = Column(String(20), default="normal")  # normal, urgent

    # 审批流程
    status = Column(String(20), default="pending")  # pending, clerk_approved, finance_approved, completed, rejected
    clerk_approval = Column(JSON, nullable=True)  # 数据员审批信息
    finance_approval = Column(JSON, nullable=True)  # 财务审批信息

    # 费用计算
    fee_rate = Column(Numeric(5, 4), nullable=False)  # 手续费率
    fee_amount = Column(Numeric(15, 2), nullable=False)  # 手续费金额
    total_amount = Column(Numeric(15, 2), nullable=False)  # 总金额

    # 执行信息
    payment_method = Column(String(50), nullable=True)
    transaction_id = Column(String(255), nullable=True)
    completed_at = Column(DateTime, nullable=True)
```

#### 流程实现

```python
# routers/topups.py
@router.post("/request")
async def create_topup_request(
    request: TopupRequest,
    current_user: User = Depends(get_current_user)
):
    """投手提交充值申请"""

    # 验证投手权限
    if current_user.role != "media_buyer":
        raise HTTPException(403, "只有投手可以提交充值申请")

    # 获取账户信息
    account = db.query(AdAccount).filter(
        AdAccount.id == request.ad_account_id,
        AdAccount.assigned_user_id == current_user.id
    ).first()

    if not account:
        raise HTTPException(404, "账户不存在或无权限")

    # 获取渠道费率
    channel = db.query(Channel).filter(Channel.id == account.channel_id).first()
    fee_rate = channel.service_fee_rate

    # 计算费用
    fee_amount = request.amount * fee_rate
    total_amount = request.amount + fee_amount

    # 创建充值申请
    topup = Topup(
        project_id=account.project_id,
        ad_account_id=request.ad_account_id,
        requested_by=current_user.id,
        amount=request.amount,
        purpose=request.purpose,
        fee_rate=fee_rate,
        fee_amount=fee_amount,
        total_amount=total_amount
    )

    db.add(topup)
    db.commit()

    # 通知数据员
    await notify_data_clerk_for_approval(topup)

    return {"message": "充值申请提交成功", "id": topup.id}

@router.put("/{topup_id}/clerk-approval")
async def clerk_approval(
    topup_id: str,
    approval: ClerkApproval,
    current_user: User = Depends(get_current_user)
):
    """数据员审批"""

    # 验证权限
    if current_user.role not in ["data_clerk", "admin"]:
        raise HTTPException(403, "权限不足")

    topup = db.query(Topup).filter(Topup.id == topup_id).first()
    if not topup:
        raise HTTPException(404, "充值申请不存在")

    # 更新审批状态
    if approval.approved:
        topup.status = "clerk_approved"
        topup.clerk_approval = {
            "approved_by": current_user.id,
            "approved_at": datetime.utcnow().isoformat(),
            "notes": approval.notes,
            "recommended_amount": approval.recommended_amount
        }

        # 通知财务审批
        await notify_finance_for_approval(topup)
    else:
        topup.status = "rejected"
        topup.clerk_approval = {
            "rejected_by": current_user.id,
            "rejected_at": datetime.utcnow().isoformat(),
            "reason": approval.reason
        }

    db.commit()
    return {"message": "数据员审批完成"}

@router.put("/{topup_id}/finance-approval")
async def finance_approval(
    topup_id: str,
    approval: FinanceApproval,
    current_user: User = Depends(get_current_user)
):
    """财务审批和执行"""

    # 验证权限
    if current_user.role not in ["finance", "admin"]:
        raise HTTPException(403, "权限不足")

    topup = db.query(Topup).filter(Topup.id == topup_id).first()
    if not topup:
        raise HTTPException(404, "充值申请不存在")

    if approval.approved:
        # 执行充值
        topup.status = "completed"
        topup.finance_approval = {
            "approved_by": current_user.id,
            "approved_at": datetime.utcnow().isoformat(),
            "payment_method": approval.payment_method,
            "transaction_id": approval.transaction_id
        }
        topup.completed_at = datetime.utcnow()

        # 更新账户余额
        await update_account_balance(topup.ad_account_id, topup.amount)

        # 记录财务流水
        await create_financial_transaction(topup)
    else:
        topup.status = "rejected"
        topup.finance_approval = {
            "rejected_by": current_user.id,
            "rejected_at": datetime.utcnow().isoformat(),
            "reason": approval.reason
        }

    db.commit()
    return {"message": "财务审批完成"}
```

### 4.4 对账机制业务逻辑

#### 对账算法

```python
# services/reconciliation_service.py
class ReconciliationService:

    def __init__(self, db_session):
        self.db = db_session

    async def monthly_reconciliation(self, project_id: str, year: int, month: int):
        """月度对账"""

        # 获取时间范围
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)

        # 1. 统计充值总额
        total_topups = self.db.query(func.sum(Topup.total_amount)).filter(
            Topup.project_id == project_id,
            Topup.status == "completed",
            Topup.completed_at >= start_date,
            Topup.completed_at < end_date
        ).scalar() or 0

        # 2. 统计消耗总额
        total_spend = self.db.query(func.sum(AdSpendDaily.spend)).filter(
            AdSpendDaily.project_id == project_id,
            AdSpendDaily.date >= start_date.date(),
            AdSpendDaily.date < end_date.date()
        ).scalar() or 0

        # 3. 计算差异
        difference = total_topups - total_spend

        # 4. 分析差异原因
        variance_analysis = await self.analyze_variance(
            project_id, start_date, end_date, difference
        )

        # 5. 生成对账报告
        reconciliation = Reconciliation(
            project_id=project_id,
            period_type="monthly",
            period_start=start_date,
            period_end=end_date - timedelta(days=1),
            total_topups=total_topups,
            total_spend=total_spend,
            difference=difference,
            variance_analysis=variance_analysis
        )

        self.db.add(reconciliation)
        self.db.commit()

        return reconciliation

    async def analyze_variance(self, project_id: str, start_date: datetime,
                            end_date: datetime, difference: float):
        """分析差异原因"""

        analysis = {
            "time_delay": 0,  # 时间差导致的差异
            "processing_fees": 0,  # 手续费
            "pending_transactions": 0,  # 待处理交易
            "other": 0  # 其他原因
        }

        # 检查时间差
        pending_topups = self.db.query(func.sum(Topup.total_amount)).filter(
            Topup.project_id == project_id,
            Topup.status == "finance_approved",
            Topup.completed_at >= start_date,
            Topup.completed_at < end_date
        ).scalar() or 0

        analysis["time_delay"] = pending_topups

        # 检查手续费
        total_fees = self.db.query(func.sum(Topup.fee_amount)).filter(
            Topup.project_id == project_id,
            Topup.status == "completed",
            Topup.completed_at >= start_date,
            Topup.completed_at < end_date
        ).scalar() or 0

        analysis["processing_fees"] = total_fees

        # 其他差异
        analysis["other"] = difference - sum(analysis.values())

        return analysis
```

---

## 5. 核心模块开发指南

### 5.1 项目管理模块

#### 功能特性
- 项目创建、编辑、删除
- 客户信息管理
- 收费模式配置
- 预算和目标管理

#### 关键代码实现

```python
# routers/projects.py
@router.post("/", response_model=ProjectResponse)
async def create_project(
    project: ProjectCreate,
    current_user: User = Depends(get_current_user)
):
    """创建项目"""

    # 验证权限
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(403, "权限不足")

    # 创建项目
    db_project = Project(
        name=project.name,
        client_name=project.client_name,
        pricing_model=project.pricing_model,
        lead_price=project.lead_price,
        setup_fee=project.setup_fee,
        monthly_budget=project.monthly_budget,
        created_by=current_user.id
    )

    db.add(db_project)
    db.commit()
    db.refresh(db_project)

    # 记录审计日志
    audit_logger.log_create(
        table_name="projects",
        record_id=str(db_project.id),
        new_values=project.dict(),
        user_id=current_user.id
    )

    return db_project

@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """获取项目列表"""

    query = db.query(Project)

    # 根据用户角色过滤
    if current_user.role == "media_buyer":
        # 投手只能看到分配给自己的项目
        query = query.join(AdAccount).filter(
            AdAccount.assigned_user_id == current_user.id
        )
    elif current_user.role in ["data_clerk", "finance"]:
        # 数据员和财务可以看到所有项目
        pass

    # 状态过滤
    if status:
        query = query.filter(Project.status == status)

    projects = query.offset(skip).limit(limit).all()
    return projects
```

### 5.2 渠道管理模块

#### 功能特性
- 代理商信息管理
- 质量评估系统
- 费用结构配置
- 表现统计分析

#### 质量评估实现

```python
# services/channel_service.py
class ChannelService:

    async def evaluate_channel_quality(self, channel_id: str):
        """评估渠道质量"""

        # 获取渠道账户数据
        accounts = db.query(AdAccount).filter(
            AdAccount.channel_id == channel_id
        ).all()

        if not accounts:
            return {"score": 0, "details": "无账户数据"}

        # 计算存活率
        total_accounts = len(accounts)
        active_accounts = len([a for a in accounts if a.status == "active"])
        survival_rate = active_accounts / total_accounts if total_accounts > 0 else 0

        # 计算平均寿命
        lifetimes = []
        for account in accounts:
            if account.dead_date:
                lifetime = (account.dead_date - account.created_date).days
                lifetimes.append(lifetime)

        avg_lifetime = sum(lifetimes) / len(lifetimes) if lifetimes else 0

        # 计算综合评分
        quality_score = (
            survival_rate * 0.4 +  # 存活率权重40%
            min(avg_lifetime / 30, 1) * 0.3 +  # 平均寿命权重30%
            self.calculate_price_competitiveness(channel_id) * 0.3  # 价格竞争力权重30%
        )

        # 更新渠道评分
        channel = db.query(Channel).filter(Channel.id == channel_id).first()
        channel.quality_score = quality_score
        channel.total_accounts = total_accounts
        channel.active_accounts = active_accounts

        db.commit()

        return {
            "score": quality_score,
            "survival_rate": survival_rate,
            "avg_lifetime": avg_lifetime,
            "total_accounts": total_accounts,
            "active_accounts": active_accounts
        }

    def calculate_price_competitiveness(self, channel_id: str):
        """计算价格竞争力"""

        channel = db.query(Channel).filter(Channel.id == channel_id).first()

        # 获取所有渠道的平均费率
        avg_fee_rate = db.query(func.avg(Channel.service_fee_rate)).scalar() or 0.1

        # 计算竞争力 (费率越低竞争力越高)
        if channel.service_fee_rate <= avg_fee_rate:
            return 1.0
        else:
            return max(0, 1 - (channel.service_fee_rate - avg_fee_rate) / avg_fee_rate)
```

### 5.3 广告账户管理模块

#### 功能特性
- 账户生命周期管理
- 状态跟踪和预警
- 预算监控
- 性能分析

#### 生命周期管理实现

```python
# services/account_service.py
class AccountService:

    async def update_account_status(self, account_id: str, new_status: str,
                                  reason: str = None, user_id: str = None):
        """更新账户状态"""

        account = db.query(AdAccount).filter(AdAccount.id == account_id).first()
        if not account:
            raise HTTPException(404, "账户不存在")

        old_status = account.status

        # 更新状态
        account.status = new_status
        account.status_reason = reason
        account.last_status_change = datetime.utcnow()

        # 更新时间戳
        if new_status == "active" and old_status != "active":
            account.activated_date = datetime.utcnow()
        elif new_status == "suspended":
            account.suspended_date = datetime.utcnow()
        elif new_status == "dead":
            account.dead_date = datetime.utcnow()
        elif new_status == "archived":
            account.archived_date = datetime.utcnow()

        # 记录状态变更历史
        status_history = AccountStatusHistory(
            account_id=account_id,
            old_status=old_status,
            new_status=new_status,
            change_reason=reason,
            changed_at=datetime.utcnow(),
            changed_by=user_id
        )

        db.add(status_history)

        # 记录审计日志
        audit_logger.log_update(
            table_name="ad_accounts",
            record_id=account_id,
            old_values={"status": old_status},
            new_values={"status": new_status, "reason": reason},
            user_id=user_id
        )

        db.commit()

        # 发送通知
        await notify_account_status_change(account, old_status, new_status)

        return account

    async def check_account_alerts(self):
        """检查账户预警"""

        # 检查预算预警
        accounts = db.query(AdAccount).filter(
            AdAccount.status == "active",
            AdAccount.auto_monitoring == True
        ).all()

        for account in accounts:
            alerts = []

            # 预算使用率预警
            if account.remaining_budget and account.daily_budget:
                usage_rate = 1 - (account.remaining_budget / account.total_budget)
                if usage_rate > 0.8:
                    alerts.append({
                        "type": "budget_exceeded",
                        "severity": "high",
                        "message": f"账户 {account.name} 预算使用率已达 {usage_rate:.1%}"
                    })

            # 性能预警
            if account.avg_cpl and account.target_cpl:
                if account.avg_cpl > account.target_cpl * 1.5:
                    alerts.append({
                        "type": "high_cpl",
                        "severity": "medium",
                        "message": f"账户 {account.name} 单粉成本过高: {account.avg_cpl}"
                    })

            # 创建预警记录
            for alert_data in alerts:
                alert = AccountAlert(
                    account_id=account.id,
                    alert_type=alert_data["type"],
                    severity=alert_data["severity"],
                    title=f"账户预警: {alert_data['type']}",
                    message=alert_data["message"],
                    status="active"
                )
                db.add(alert)

        if alerts:
            db.commit()
            await send_alert_notifications(alerts)
```

### 5.4 权限管理模块

#### 角色权限矩阵

| 功能模块 | 管理员 | 项目经理 | 数据员 | 财务 | 投手 |
|---------|--------|----------|--------|------|------|
| 项目管理 | 全部 | 读写 | 只读 | 只读 | 只读(自己的) |
| 渠道管理 | 全部 | 读写 | 读写 | 只读 | 无 |
| 账户管理 | 全部 | 读写 | 读写 | 只读 | 只读(自己的) |
| 日报管理 | 全部 | 读写 | 读写 | 只读 | 读写(自己的) |
| 充值管理 | 全部 | 只读 | 审核 | 审批执行 | 申请 |
| 对账管理 | 全部 | 只读 | 只读 | 读写 | 无 |

#### 权限实现

```python
# core/permissions.py
class PermissionChecker:

    @staticmethod
    def can_access_project(user: User, project_id: str, action: str) -> bool:
        """检查项目访问权限"""

        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return False

        # 管理员拥有所有权限
        if user.role == "admin":
            return True

        # 项目经理可以管理自己的项目
        if user.role == "manager" and project.manager_id == user.id:
            return True

        # 投手只能查看分配给自己的项目
        if user.role == "media_buyer":
            account = db.query(AdAccount).filter(
                AdAccount.project_id == project_id,
                AdAccount.assigned_user_id == user.id
            ).first()
            return account is not None and action in ["read"]

        # 其他角色根据具体权限判断
        return action in ["read"]

    @staticmethod
    def can_manage_account(user: User, account_id: str, action: str) -> bool:
        """检查账户管理权限"""

        account = db.query(AdAccount).filter(AdAccount.id == account_id).first()
        if not account:
            return False

        # 管理员拥有所有权限
        if user.role == "admin":
            return True

        # 项目经理和数据员可以管理所有账户
        if user.role in ["manager", "data_clerk"]:
            return True

        # 投手只能管理分配给自己的账户
        if user.role == "media_buyer" and account.assigned_user_id == user.id:
            return action in ["read", "update_performance"]

        return False

# 权限装饰器
def require_permission(resource: str, action: str):
    """权限验证装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(401, "未认证")

            # 获取资源ID
            resource_id = kwargs.get(f"{resource}_id")
            if not resource_id:
                raise HTTPException(400, f"缺少{resource}_id参数")

            # 检查权限
            checker = PermissionChecker()
            has_permission = getattr(checker, f"can_{action}_{resource}")(current_user, resource_id, action)

            if not has_permission:
                raise HTTPException(403, "权限不足")

            return await func(*args, **kwargs)
        return wrapper
    return decorator

# 使用示例
@router.put("/accounts/{account_id}")
@require_permission(resource="account", action="update")
async def update_account(
    account_id: str,
    account_update: AccountUpdate,
    current_user: User = Depends(get_current_user)
):
    """更新账户信息"""
    # 业务逻辑...
    pass
```

---

## 6. 数据模型与API设计

### 6.1 数据库设计

#### 核心表结构

```sql
-- 项目表
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    client_name VARCHAR(255) NOT NULL,
    pricing_model VARCHAR(50) DEFAULT 'per_lead',
    lead_price DECIMAL(10,2) NOT NULL,
    setup_fee DECIMAL(10,2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'planning',
    monthly_budget DECIMAL(12,2),
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 渠道表
CREATE TABLE channels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    service_fee_rate DECIMAL(5,4) NOT NULL, -- 0.05 = 5%
    account_setup_fee DECIMAL(10,2) DEFAULT 0,
    quality_score DECIMAL(3,2), -- 0-10分
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW()
);

-- 广告账户表
CREATE TABLE ad_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    project_id UUID REFERENCES projects(id),
    channel_id UUID REFERENCES channels(id),
    assigned_user_id UUID REFERENCES users(id),
    status VARCHAR(20) DEFAULT 'new',
    daily_budget DECIMAL(10,2),
    total_budget DECIMAL(12,2),
    remaining_budget DECIMAL(12,2),
    currency VARCHAR(3) DEFAULT 'USD',
    total_spend DECIMAL(15,2) DEFAULT 0,
    total_leads INTEGER DEFAULT 0,
    avg_cpl DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 每日消耗表
CREATE TABLE ad_spend_daily (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id),
    ad_account_id UUID REFERENCES ad_accounts(id),
    user_id UUID REFERENCES users(id),
    date DATE NOT NULL,
    leads_submitted INTEGER DEFAULT 0,
    leads_confirmed INTEGER,
    spend DECIMAL(15,2) NOT NULL,
    confirmed_by UUID REFERENCES users(id),
    confirmed_at TIMESTAMP,
    leads_diff INTEGER,
    diff_reason TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 充值表
CREATE TABLE topups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id),
    ad_account_id UUID REFERENCES ad_accounts(id),
    requested_by UUID REFERENCES users(id),
    amount DECIMAL(15,2) NOT NULL,
    purpose TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    fee_rate DECIMAL(5,4) NOT NULL,
    fee_amount DECIMAL(15,2) NOT NULL,
    total_amount DECIMAL(15,2) NOT NULL,
    clerk_approval JSONB,
    finance_approval JSONB,
    transaction_id VARCHAR(255),
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 索引设计

```sql
-- 性能优化索引
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_client ON projects(client_name);
CREATE INDEX idx_ad_accounts_project ON ad_accounts(project_id);
CREATE INDEX idx_ad_accounts_user ON ad_accounts(assigned_user_id);
CREATE INDEX idx_ad_accounts_status ON ad_accounts(status);
CREATE INDEX idx_ad_spend_daily_date ON ad_spend_daily(date);
CREATE INDEX idx_ad_spend_daily_project ON ad_spend_daily(project_id);
CREATE INDEX idx_ad_spend_daily_user ON ad_spend_daily(user_id);
CREATE INDEX idx_topups_status ON topups(status);
CREATE INDEX idx_topups_project ON topups(project_id);
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at);
```

### 6.2 API接口设计

#### RESTful API规范

```
# 项目管理
GET    /api/projects              # 获取项目列表
POST   /api/projects              # 创建项目
GET    /api/projects/{id}         # 获取项目详情
PUT    /api/projects/{id}         # 更新项目
DELETE /api/projects/{id}         # 删除项目

# 渠道管理
GET    /api/channels              # 获取渠道列表
POST   /api/channels              # 创建渠道
GET    /api/channels/{id}         # 获取渠道详情
PUT    /api/channels/{id}         # 更新渠道
POST   /api/channels/{id}/evaluate # 评估渠道质量

# 广告账户管理
GET    /api/accounts              # 获取账户列表
POST   /api/accounts              # 创建账户
GET    /api/accounts/{id}         # 获取账户详情
PUT    /api/accounts/{id}         # 更新账户
PUT    /api/accounts/{id}/status  # 更新账户状态
GET    /api/accounts/{id}/performance # 获取账户表现

# 日报管理
GET    /api/daily-reports         # 获取日报列表
POST   /api/daily-reports         # 提交日报
PUT    /api/daily-reports/{id}/confirm # 确认粉数
GET    /api/daily-reports/summary  # 获取汇总数据

# 充值管理
GET    /api/topups                # 获取充值列表
POST   /api/topups/request        # 申请充值
PUT    /api/topups/{id}/clerk-approval  # 数据员审批
PUT    /api/topups/{id}/finance-approval # 财务审批
GET    /api/topups/summary        # 充值汇总

# 对账管理
GET    /api/reconciliation        # 获取对账记录
POST   /api/reconciliation/monthly # 月度对账
GET    /api/reconciliation/{id}/report  # 对账报告

# 用户认证
POST   /api/auth/login            # 用户登录
POST   /api/auth/logout           # 用户登出
GET    /api/auth/me               # 获取当前用户信息
PUT    /api/auth/password         # 修改密码
```

#### API响应格式

```python
# 成功响应
{
    "success": true,
    "data": {
        // 实际数据
    },
    "message": "操作成功",
    "timestamp": "2025-11-10T10:30:00Z"
}

# 错误响应
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "输入数据验证失败",
        "details": {
            "field": "email",
            "reason": "邮箱格式不正确"
        }
    },
    "timestamp": "2025-11-10T10:30:00Z"
}

# 分页响应
{
    "success": true,
    "data": {
        "items": [...],
        "pagination": {
            "page": 1,
            "size": 20,
            "total": 100,
            "pages": 5
        }
    }
}
```

### 6.3 数据验证与安全

#### Pydantic模型

```python
# schemas/projects.py
from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime

class ProjectBase(BaseModel):
    name: str
    client_name: str
    pricing_model: str = "per_lead"
    lead_price: float
    setup_fee: float = 0
    monthly_budget: Optional[float] = None
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    @validator('lead_price')
    def lead_price_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('单粉价格必须大于0')
        return v

    @validator('pricing_model')
    def validate_pricing_model(cls, v):
        if v not in ['per_lead', 'fixed_fee', 'hybrid']:
            raise ValueError('无效的收费模式')
        return v

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    client_name: Optional[str] = None
    status: Optional[str] = None
    monthly_budget: Optional[float] = None

    @validator('status')
    def validate_status(cls, v):
        if v and v not in ['planning', 'active', 'paused', 'completed', 'cancelled']:
            raise ValueError('无效的项目状态')
        return v

class ProjectResponse(ProjectBase):
    id: str
    status: str
    created_at: datetime
    updated_at: datetime
    manager: Optional[dict] = None

    class Config:
        from_attributes = True
```

#### 数据库安全

```sql
-- 行级安全策略 (RLS)
-- 启用RLS
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE ad_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE ad_spend_daily ENABLE ROW LEVEL SECURITY;

-- 项目访问策略
CREATE POLICY project_access_policy ON projects
    USING (
        -- 管理员可以访问所有项目
        created_by = current_setting('app.current_user_id')::uuid
        OR
        -- 项目经理可以访问自己的项目
        manager_id = current_setting('app.current_user_id')::uuid
        OR
        -- 投手可以访问分配给自己的项目
        EXISTS (
            SELECT 1 FROM ad_accounts
            WHERE ad_accounts.project_id = projects.id
            AND ad_accounts.assigned_user_id = current_setting('app.current_user_id')::uuid
        )
    );

-- 账户访问策略
CREATE POLICY account_access_policy ON ad_accounts
    USING (
        -- 管理员可以访问所有账户
        current_setting('app.current_role') = 'admin'
        OR
        -- 项目经理和数据员可以访问所有账户
        current_setting('app.current_role') IN ('manager', 'data_clerk')
        OR
        -- 投手只能访问分配给自己的账户
        assigned_user_id = current_setting('app.current_user_id')::uuid
    );
```

---

## 7. 前端开发实现

### 7.1 项目结构

```
app/
├── layout.tsx                 # 根布局
├── page.tsx                   # 首页
├── globals.css                # 全局样式
├── components/                # 组件库
│   ├── ui/                    # 基础UI组件
│   │   ├── button.tsx
│   │   ├── input.tsx
│   │   ├── table.tsx
│   │   └── modal.tsx
│   ├── auth/                  # 认证组件
│   │   ├── login-form.tsx
│   │   └── protected-route.tsx
│   └── business/              # 业务组件
│       ├── project-card.tsx
│       ├── account-table.tsx
│       └── topup-form.tsx
├── lib/                       # 工具库
│   ├── api.ts                 # API客户端
│   ├── auth.ts                # 认证工具
│   └── utils.ts               # 通用工具
├── hooks/                     # 自定义Hook
│   ├── use-auth.ts
│   ├── use-api.ts
│   └── use-permissions.ts
└── app/                       # 页面路由
    ├── auth/
    ├── projects/
    ├── accounts/
    ├── finance/
    └── reports/
```

### 7.2 认证实现

```typescript
// lib/auth.ts
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

export interface User {
  id: string
  email: string
  role: 'admin' | 'manager' | 'data_clerk' | 'finance' | 'media_buyer'
  name: string
}

export async function signIn(email: string, password: string) {
  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password,
  })

  if (error) throw error

  // 获取用户角色等信息
  const { data: userData } = await supabase
    .from('users')
    .select('*')
    .eq('id', data.user?.id)
    .single()

  return { ...data, user: { ...data.user, ...userData } }
}

export async function signOut() {
  const { error } = await supabase.auth.signOut()
  if (error) throw error
}

// hooks/use-auth.ts
import { createContext, useContext, useEffect, useState } from 'react'
import { User, supabase } from '@/lib/auth'

interface AuthContextType {
  user: User | null
  loading: boolean
  signIn: (email: string, password: string) => Promise<void>
  signOut: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // 获取初始会话
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session?.user) {
        fetchUser(session.user.id).then(setUser)
      }
      setLoading(false)
    })

    // 监听认证状态变化
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        if (session?.user) {
          const userData = await fetchUser(session.user.id)
          setUser(userData)
        } else {
          setUser(null)
        }
        setLoading(false)
      }
    )

    return () => subscription.unsubscribe()
  }, [])

  async function fetchUser(userId: string): Promise<User | null> {
    const { data } = await supabase
      .from('users')
      .select('*')
      .eq('id', userId)
      .single()

    return data
  }

  const value = {
    user,
    loading,
    signIn: async (email: string, password: string) => {
      const { data } = await signIn(email, password)
      setUser(data.user as User)
    },
    signOut: async () => {
      await signOut()
      setUser(null)
    }
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
```

### 7.3 API客户端

```typescript
// lib/api.ts
import { useAuth } from '@/hooks/use-auth'

class ApiClient {
  private baseURL: string

  constructor(baseURL: string = '/api') {
    this.baseURL = baseURL
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const { user } = useAuth()

    const url = `${this.baseURL}${endpoint}`
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    }

    // 添加认证头
    if (user?.id) {
      config.headers = {
        ...config.headers,
        Authorization: `Bearer ${await getAuthToken()}`
      }
    }

    const response = await fetch(url, config)

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.message || 'API请求失败')
    }

    return response.json()
  }

  // 项目相关API
  async getProjects(params?: {
    skip?: number
    limit?: number
    status?: string
  }) {
    const searchParams = new URLSearchParams(params as any).toString()
    return this.request(`/projects?${searchParams}`)
  }

  async createProject(data: ProjectCreate) {
    return this.request('/projects', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async updateProject(id: string, data: ProjectUpdate) {
    return this.request(`/projects/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  // 账户相关API
  async getAccounts(params?: {
    projectId?: string
    userId?: string
    status?: string
  }) {
    const searchParams = new URLSearchParams(params as any).toString()
    return this.request(`/accounts?${searchParams}`)
  }

  async updateAccountStatus(id: string, status: string, reason?: string) {
    return this.request(`/accounts/${id}/status`, {
      method: 'PUT',
      body: JSON.stringify({ status, reason }),
    })
  }

  // 日报相关API
  async submitDailyReport(data: DailyReportCreate) {
    return this.request('/daily-reports', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async confirmDailyReport(id: string, data: { leads_confirmed: number, reason?: string }) {
    return this.request(`/daily-reports/${id}/confirm`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  // 充值相关API
  async createTopupRequest(data: TopupRequest) {
    return this.request('/topups/request', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async clerkApproval(id: string, data: ClerkApproval) {
    return this.request(`/topups/${id}/clerk-approval`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async financeApproval(id: string, data: FinanceApproval) {
    return this.request(`/topups/${id}/finance-approval`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }
}

export const apiClient = new ApiClient()

// hooks/use-api.ts
import { useState, useEffect } from 'react'
import { apiClient } from '@/lib/api'

export function useApi<T>(
  apiCall: () => Promise<T>,
  dependencies: any[] = []
) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    let cancelled = false

    async function fetchData() {
      try {
        setLoading(true)
        setError(null)
        const result = await apiCall()
        if (!cancelled) {
          setData(result)
        }
      } catch (err) {
        if (!cancelled) {
          setError(err as Error)
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    fetchData()

    return () => {
      cancelled = true
    }
  }, dependencies)

  return { data, loading, error, refetch: () => fetchData() }
}
```

### 7.4 业务组件示例

```typescript
// components/business/project-card.tsx
import { Project } from '@/types'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { formatCurrency, formatDate } from '@/lib/utils'

interface ProjectCardProps {
  project: Project
  onEdit?: (project: Project) => void
  onDelete?: (project: Project) => void
}

export function ProjectCard({ project, onEdit, onDelete }: ProjectCardProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800'
      case 'planning': return 'bg-blue-100 text-blue-800'
      case 'paused': return 'bg-yellow-100 text-yellow-800'
      case 'completed': return 'bg-gray-100 text-gray-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'active': return '进行中'
      case 'planning': return '规划中'
      case 'paused': return '暂停'
      case 'completed': return '已完成'
      default: return status
    }
  }

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">{project.name}</CardTitle>
          <Badge className={getStatusColor(project.status)}>
            {getStatusText(project.status)}
          </Badge>
        </div>
        <p className="text-sm text-gray-600">
          客户: {project.client_name}
        </p>
      </CardHeader>

      <CardContent>
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span>收费模式:</span>
            <span>{project.pricing_model === 'per_lead' ? '按粉计费' : '固定费用'}</span>
          </div>

          {project.pricing_model === 'per_lead' && (
            <div className="flex justify-between text-sm">
              <span>单粉价格:</span>
              <span>{formatCurrency(project.lead_price)}</span>
            </div>
          )}

          {project.monthly_budget && (
            <div className="flex justify-between text-sm">
              <span>月度预算:</span>
              <span>{formatCurrency(project.monthly_budget)}</span>
            </div>
          )}

          <div className="flex justify-between text-sm">
            <span>创建时间:</span>
            <span>{formatDate(project.created_at)}</span>
          </div>
        </div>

        <div className="flex gap-2 mt-4">
          {onEdit && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => onEdit(project)}
            >
              编辑
            </Button>
          )}

          {onDelete && (
            <Button
              variant="destructive"
              size="sm"
              onClick={() => onDelete(project)}
            >
              删除
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

// components/business/topup-form.tsx
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useAuth } from '@/hooks/use-auth'
import { apiClient } from '@/lib/api'

interface TopupFormProps {
  accounts: Array<{ id: string; name: string; remaining_budget: number }>
  onSuccess?: () => void
}

interface TopupFormData {
  ad_account_id: string
  amount: number
  purpose: string
  urgency_level: 'normal' | 'urgent'
}

export function TopupForm({ accounts, onSuccess }: TopupFormProps) {
  const { user } = useAuth()
  const [loading, setLoading] = useState(false)
  const [selectedAccount, setSelectedAccount] = useState<string>('')

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors }
  } = useForm<TopupFormData>()

  const watchedAccountId = watch('ad_account_id')
  const watchedAmount = watch('amount')

  // 计算预估费用
  const selectedAccountData = accounts.find(a => a.id === watchedAccountId)
  const estimatedFee = selectedAccountData && watchedAmount
    ? watchedAmount * 0.1 // 假设10%手续费
    : 0
  const totalAmount = (watchedAmount || 0) + estimatedFee

  const onSubmit = async (data: TopupFormData) => {
    try {
      setLoading(true)
      await apiClient.createTopupRequest(data)
      onSuccess?.()
    } catch (error) {
      console.error('提交充值申请失败:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>申请充值</CardTitle>
      </CardHeader>

      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <Label htmlFor="ad_account_id">广告账户</Label>
            <Select
              value={watchedAccountId}
              onValueChange={(value) => setValue('ad_account_id', value)}
            >
              <SelectTrigger>
                <SelectValue placeholder="选择广告账户" />
              </SelectTrigger>
              <SelectContent>
                {accounts.map((account) => (
                  <SelectItem key={account.id} value={account.id}>
                    {account.name} (余额: {account.remaining_budget})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {errors.ad_account_id && (
              <p className="text-red-500 text-sm mt-1">
                {errors.ad_account_id.message}
              </p>
            )}
          </div>

          <div>
            <Label htmlFor="amount">充值金额 (USD)</Label>
            <Input
              id="amount"
              type="number"
              step="0.01"
              placeholder="输入充值金额"
              {...register('amount', {
                required: '请输入充值金额',
                min: { value: 1, message: '充值金额必须大于0' }
              })}
            />
            {errors.amount && (
              <p className="text-red-500 text-sm mt-1">
                {errors.amount.message}
              </p>
            )}
          </div>

          {watchedAmount && (
            <div className="bg-gray-50 p-3 rounded-md">
              <div className="flex justify-between text-sm">
                <span>充值金额:</span>
                <span>${watchedAmount.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span>预估手续费 (10%):</span>
                <span>${estimatedFee.toFixed(2)}</span>
              </div>
              <div className="flex justify-between font-semibold border-t pt-2">
                <span>总计:</span>
                <span>${totalAmount.toFixed(2)}</span>
              </div>
            </div>
          )}

          <div>
            <Label htmlFor="purpose">充值用途</Label>
            <Textarea
              id="purpose"
              placeholder="请说明充值用途..."
              {...register('purpose', {
                required: '请说明充值用途'
              })}
            />
            {errors.purpose && (
              <p className="text-red-500 text-sm mt-1">
                {errors.purpose.message}
              </p>
            )}
          </div>

          <div>
            <Label>紧急程度</Label>
            <Select
              value={watch('urgency_level')}
              onValueChange={(value) => setValue('urgency_level', value as any)}
            >
              <SelectTrigger>
                <SelectValue placeholder="选择紧急程度" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="normal">普通</SelectItem>
                <SelectItem value="urgent">紧急</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <Button type="submit" disabled={loading} className="w-full">
            {loading ? '提交中...' : '提交申请'}
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}
```

---

## 8. 部署与运维

### 8.1 环境配置

#### 生产环境变量

```bash
# .env.production
# 数据库配置
DATABASE_URL=postgresql://user:password@host:port/database
SUPABASE_URL=your-supabase-url
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key

# JWT配置
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# API配置
API_V1_STR=/api/v1
PROJECT_NAME=AI广告代投系统
DEBUG=false

# CORS配置
BACKEND_CORS_ORIGINS=["https://yourdomain.com", "https://admin.yourdomain.com"]

# 文件上传配置
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=10485760  # 10MB

# 邮件配置
SMTP_TLS=true
SMTP_PORT=587
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# 监控配置
SENTRY_DSN=your-sentry-dsn
LOG_LEVEL=INFO
```

#### Docker配置

```dockerfile
# Dockerfile
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend
COPY app/package*.json ./
RUN npm ci --only=production

COPY app/ ./
RUN npm run build

FROM python:3.11-slim AS backend

WORKDIR /app/backend

RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./
COPY --from=frontend-builder /app/frontend/public ./public

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/ad_spend
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    volumes:
      - ./uploads:/app/uploads
      - ./logs:/app/logs

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: ad_spend
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app

volumes:
  postgres_data:
  redis_data:
```

### 8.2 Nginx配置

```nginx
# nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server app:8000;
    }

    server {
        listen 80;
        server_name yourdomain.com www.yourdomain.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name yourdomain.com www.yourdomain.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;

        # 前端静态文件
        location / {
            root /var/www/html;
            try_files $uri $uri/ /index.html;

            # 缓存静态资源
            location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
                expires 1y;
                add_header Cache-Control "public, immutable";
            }
        }

        # API代理
        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # 超时设置
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # 文件上传大小限制
        client_max_body_size 10M;

        # 安全头
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    }
}
```

### 8.3 数据库管理

#### 迁移脚本

```python
# alembic/versions/001_initial_schema.py
"""Initial schema

Revision ID: 001
Revises:
Create Date: 2025-11-10 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # 创建用户表
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=False)
    op.create_index(op.f('ix_users_role'), 'users', ['role'], unique=False)

    # 创建项目表
    op.create_table('projects',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('client_name', sa.String(length=255), nullable=False),
        sa.Column('pricing_model', sa.String(length=50), nullable=False),
        sa.Column('lead_price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('setup_fee', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('monthly_budget', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_projects_client_name'), 'projects', ['client_name'], unique=False)
    op.create_index(op.f('ix_projects_status'), 'projects', ['status'], unique=False)

    # ... 其他表的创建

def downgrade():
    op.drop_table('projects')
    op.drop_table('users')
```

#### 备份脚本

```bash
#!/bin/bash
# scripts/backup.sh

# 配置
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="ad_spend"
DB_USER="postgres"
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p $BACKUP_DIR

# 数据库备份
echo "开始数据库备份..."
pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME \
    --format=custom \
    --compress=9 \
    --file=$BACKUP_DIR/db_backup_$DATE.dump

if [ $? -eq 0 ]; then
    echo "数据库备份成功: $BACKUP_DIR/db_backup_$DATE.dump"
else
    echo "数据库备份失败!"
    exit 1
fi

# 文件备份
echo "开始文件备份..."
tar -czf $BACKUP_DIR/files_backup_$DATE.tar.gz \
    uploads/ \
    logs/ \
    .env.production

if [ $? -eq 0 ]; then
    echo "文件备份成功: $BACKUP_DIR/files_backup_$DATE.tar.gz"
else
    echo "文件备份失败!"
    exit 1
fi

# 清理旧备份 (保留7天)
find $BACKUP_DIR -name "*.dump" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "备份完成!"
```

### 8.4 监控与日志

#### 应用监控

```python
# monitoring/health_check.py
from fastapi import APIRouter, Depends
from sqlalchemy import text
from backend.core.db import get_db_session
from backend.core.redis import redis_client
import psutil
import datetime

router = APIRouter()

@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@router.get("/health/detailed")
async def detailed_health_check():
    """详细健康检查"""

    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }

    # 数据库检查
    try:
        with get_db_session() as session:
            result = session.execute(text("SELECT 1"))
            health_status["services"]["database"] = {
                "status": "healthy",
                "response_time": "< 10ms"
            }
    except Exception as e:
        health_status["services"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "unhealthy"

    # Redis检查
    try:
        redis_client.ping()
        health_status["services"]["redis"] = {
            "status": "healthy",
            "response_time": "< 5ms"
        }
    except Exception as e:
        health_status["services"]["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "unhealthy"

    # 系统资源检查
    health_status["services"]["system"] = {
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent
    }

    return health_status

@router.get("/metrics")
async def get_metrics():
    """获取系统指标"""

    # 数据库指标
    with get_db_session() as session:
        # 活跃用户数
        active_users = session.execute(text("""
            SELECT COUNT(*) FROM users WHERE is_active = true
        """)).scalar()

        # 今日数据量
        today_stats = session.execute(text("""
            SELECT
                COUNT(*) as daily_reports,
                SUM(spend) as total_spend,
                SUM(leads_confirmed) as total_leads
            FROM ad_spend_daily
            WHERE date = CURRENT_DATE
        """)).fetchone()

    # 系统指标
    system_metrics = {
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage('/').percent,
        "load_average": psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else None
    }

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "business_metrics": {
            "active_users": active_users,
            "daily_reports": today_stats.daily_reports or 0,
            "total_spend": float(today_stats.total_spend or 0),
            "total_leads": today_stats.total_leads or 0
        },
        "system_metrics": system_metrics
    }
```

#### 日志配置

```python
# logging_config.py
import logging
import logging.config
from pathlib import Path

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s",
        },
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(module)s %(funcName)s %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "default",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": "logs/app.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "encoding": "utf8"
        },
        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "formatter": "detailed",
            "filename": "logs/error.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "encoding": "utf8"
        },
        "audit_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "json",
            "filename": "logs/audit.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 30,
            "encoding": "utf8"
        }
    },
    "loggers": {
        "": {  # root logger
            "level": "INFO",
            "handlers": ["console", "file", "error_file"]
        },
        "audit": {
            "level": "INFO",
            "handlers": ["audit_file"],
            "propagate": False
        },
        "uvicorn": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False
        },
        "sqlalchemy.engine": {
            "level": "WARNING",
            "handlers": ["file"],
            "propagate": False
        }
    }
}

def setup_logging():
    """设置日志配置"""
    # 创建日志目录
    Path("logs").mkdir(exist_ok=True)

    # 应用配置
    logging.config.dictConfig(LOGGING_CONFIG)
```

---

## 9. 测试与质量保证

### 9.1 测试策略

#### 测试金字塔

```
    /\
   /  \     E2E Tests (10%)
  /____\
 /      \   Integration Tests (20%)
/__________\ Unit Tests (70%)
```

#### 单元测试

```python
# tests/test_projects_service.py
import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from backend.services.project_service import ProjectService
from backend.models.projects import Project

class TestProjectService:

    @pytest.fixture
    def project_service(self):
        """创建项目服务实例"""
        mock_db = Mock()
        return ProjectService(mock_db)

    @pytest.fixture
    def sample_project(self):
        """示例项目数据"""
        return Project(
            id="test-project-id",
            name="测试项目",
            client_name="测试客户",
            pricing_model="per_lead",
            lead_price=10.0,
            setup_fee=1000.0,
            status="planning"
        )

    def test_create_project_success(self, project_service, sample_project):
        """测试创建项目成功"""
        # 模拟数据库操作
        project_service.db.add.return_value = None
        project_service.db.commit.return_value = None
        project_service.db.refresh.return_value = None

        # 执行测试
        result = project_service.create_project({
            "name": "测试项目",
            "client_name": "测试客户",
            "pricing_model": "per_lead",
            "lead_price": 10.0,
            "setup_fee": 1000.0
        }, user_id="test-user-id")

        # 验证结果
        assert result is not None
        assert result.name == "测试项目"
        assert result.client_name == "测试客户"
        project_service.db.add.assert_called_once()
        project_service.db.commit.assert_called_once()

    def test_create_project_invalid_pricing_model(self, project_service):
        """测试创建项目失败 - 无效收费模式"""
        with pytest.raises(ValueError, match="无效的收费模式"):
            project_service.create_project({
                "name": "测试项目",
                "client_name": "测试客户",
                "pricing_model": "invalid_model",
                "lead_price": 10.0
            }, user_id="test-user-id")

    def test_update_project_status_success(self, project_service, sample_project):
        """测试更新项目状态成功"""
        # 模拟数据库查询
        project_service.db.query.return_value.filter.return_value.first.return_value = sample_project

        # 执行测试
        result = project_service.update_project_status(
            "test-project-id",
            "active",
            user_id="test-user-id"
        )

        # 验证结果
        assert result.status == "active"
        project_service.db.commit.assert_called_once()

    def test_calculate_project_roi(self, project_service):
        """测试项目ROI计算"""
        # 模拟数据
        project_service.db.query.return_value.filter.return_value.scalar.side_effect = [
            1000.0,  # 总收入 (100个粉 * $10)
            600.0    # 总成本 (广告费 $500 + 手续费 $100)
        ]

        # 执行测试
        roi = project_service.calculate_project_roi("test-project-id")

        # 验证结果
        expected_roi = ((1000.0 - 600.0) / 600.0) * 100  # 66.67%
        assert abs(roi - expected_roi) < 0.01
```

#### 集成测试

```python
# tests/test_api_integration.py
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.core.db import get_db_session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 测试数据库
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db_session] = override_get_db

client = TestClient(app)

class TestProjectAPI:

    def test_create_project_api(self):
        """测试创建项目API"""
        # 先登录获取token
        login_response = client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "testpassword"
        })
        token = login_response.json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}

        # 创建项目
        project_data = {
            "name": "API测试项目",
            "client_name": "API测试客户",
            "pricing_model": "per_lead",
            "lead_price": 15.0,
            "setup_fee": 2000.0,
            "monthly_budget": 10000.0
        }

        response = client.post("/api/projects", json=project_data, headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "API测试项目"
        assert data["client_name"] == "API测试客户"
        assert "id" in data

    def test_get_projects_api(self):
        """测试获取项目列表API"""
        # 登录
        login_response = client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "testpassword"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 获取项目列表
        response = client.get("/api/projects", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "pagination" in data
        assert isinstance(data["items"], list)

    def test_unauthorized_access(self):
        """测试未授权访问"""
        response = client.get("/api/projects")
        assert response.status_code == 401

        response = client.post("/api/projects", json={
            "name": "未授权项目"
        })
        assert response.status_code == 401
```

#### E2E测试

```python
# tests/test_e2e_workflows.py
import pytest
from playwright.sync_api import Page, expect

class TestE2EWorkflows:

    def test_complete_topup_workflow(self, page: Page):
        """测试完整的充值流程"""

        # 1. 登录
        page.goto("http://localhost:3000/login")
        page.fill("input[name='email']", "media_buyer@test.com")
        page.fill("input[name='password']", "testpassword")
        page.click("button[type='submit']")

        # 验证登录成功
        expect(page).to_have_url("http://localhost:3000/dashboard")

        # 2. 导航到财务管理
        page.click("text=财务管理")
        page.click("text=充值申请")

        # 3. 创建充值申请
        page.click("text=新建申请")
        page.select_option("select[name='ad_account_id']", "测试账户1")
        page.fill("input[name='amount']", "1000")
        page.fill("textarea[name='purpose']", "用于Facebook广告投放")
        page.click("button[type='submit']")

        # 4. 验证申请创建成功
        expect(page.locator("text=申请提交成功")).to_be_visible()

        # 5. 切换到数据员账号
        page.click("text=退出登录")
        page.fill("input[name='email']", "data_clerk@test.com")
        page.fill("input[name='password']", "testpassword")
        page.click("button[type='submit']")

        # 6. 审批充值申请
        page.goto("http://localhost:3000/finance/topups")
        page.click("text=待审批")
        page.click("text=审批")
        page.fill("textarea[name='notes']", "预算充足，建议批准")
        page.click("button:has-text('批准')")

        # 7. 验证审批成功
        expect(page.locator("text=审批成功")).to_be_visible()

        # 8. 切换到财务账号
        page.click("text=退出登录")
        page.fill("input[name='email']", "finance@test.com")
        page.fill("input[name='password']", "testpassword")
        page.click("button[type='submit']")

        # 9. 财务最终审批
        page.goto("http://localhost:3000/finance/topups")
        page.click("text=待审批")
        page.click("text=审批")
        page.select_option("select[name='payment_method']", "银行转账")
        page.fill("input[name='transaction_id']", "TXN123456")
        page.click("button:has-text('批准并执行')")

        # 10. 验证完成
        expect(page.locator("text=充值完成")).to_be_visible()
```

### 9.2 性能测试

#### 负载测试

```python
# tests/test_performance.py
import asyncio
import aiohttp
import time
from concurrent.futures import ThreadPoolExecutor
import statistics

class PerformanceTest:

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.results = []

    async def single_request(self, session: aiohttp.ClientSession, endpoint: str):
        """单个请求测试"""
        start_time = time.time()
        try:
            async with session.get(f"{self.base_url}{endpoint}") as response:
                await response.text()
                end_time = time.time()
                return {
                    "status_code": response.status,
                    "response_time": end_time - start_time,
                    "success": response.status == 200
                }
        except Exception as e:
            end_time = time.time()
            return {
                "status_code": 0,
                "response_time": end_time - start_time,
                "success": False,
                "error": str(e)
            }

    async def load_test(self, endpoint: str, concurrent_users: int = 10, requests_per_user: int = 5):
        """负载测试"""
        print(f"开始负载测试: {concurrent_users}个并发用户, 每用户{requests_per_user}个请求")

        async with aiohttp.ClientSession() as session:
            tasks = []
            for user in range(concurrent_users):
                for request in range(requests_per_user):
                    task = self.single_request(session, endpoint)
                    tasks.append(task)

            results = await asyncio.gather(*tasks)
            self.results.extend(results)

        # 分析结果
        successful_requests = [r for r in results if r["success"]]
        failed_requests = [r for r in results if not r["success"]]

        response_times = [r["response_time"] for r in successful_requests]

        stats = {
            "total_requests": len(results),
            "successful_requests": len(successful_requests),
            "failed_requests": len(failed_requests),
            "success_rate": len(successful_requests) / len(results) * 100,
            "avg_response_time": statistics.mean(response_times) if response_times else 0,
            "min_response_time": min(response_times) if response_times else 0,
            "max_response_time": max(response_times) if response_times else 0,
            "median_response_time": statistics.median(response_times) if response_times else 0,
            "p95_response_time": statistics.quantiles(response_times, n=20)[18] if len(response_times) > 20 else 0,
            "requests_per_second": len(results) / (max(response_times) - min(response_times)) if response_times else 0
        }

        return stats

    def print_results(self, stats: dict):
        """打印测试结果"""
        print("\n=== 性能测试结果 ===")
        print(f"总请求数: {stats['total_requests']}")
        print(f"成功请求数: {stats['successful_requests']}")
        print(f"失败请求数: {stats['failed_requests']}")
        print(f"成功率: {stats['success_rate']:.2f}%")
        print(f"平均响应时间: {stats['avg_response_time']:.3f}s")
        print(f"最小响应时间: {stats['min_response_time']:.3f}s")
        print(f"最大响应时间: {stats['max_response_time']:.3f}s")
        print(f"中位数响应时间: {stats['median_response_time']:.3f}s")
        print(f"95%响应时间: {stats['p95_response_time']:.3f}s")
        print(f"每秒请求数: {stats['requests_per_second']:.2f}")

# 使用示例
async def run_performance_tests():
    tester = PerformanceTest("http://localhost:8000")

    # 测试项目列表API
    print("测试项目列表API...")
    stats = await tester.load_test("/api/projects", concurrent_users=20, requests_per_user=10)
    tester.print_results(stats)

    # 测试账户列表API
    print("\n测试账户列表API...")
    stats = await tester.load_test("/api/accounts", concurrent_users=15, requests_per_user=8)
    tester.print_results(stats)

if __name__ == "__main__":
    asyncio.run(run_performance_tests())
```

### 9.3 质量门禁

#### CI/CD质量检查

```yaml
# .github/workflows/quality-check.yml
name: Quality Check

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-asyncio black flake8 mypy

    - name: Code formatting check
      run: |
        black --check backend/
        flake8 backend/
        mypy backend/

    - name: Run unit tests
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
        TESTING: true
      run: |
        pytest tests/unit/ -v --cov=backend --cov-report=xml --cov-fail-under=80

    - name: Run integration tests
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
        TESTING: true
      run: |
        pytest tests/integration/ -v

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella

  frontend-test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'
        cache-dependency-path: app/package-lock.json

    - name: Install dependencies
      working-directory: ./app
      run: npm ci

    - name: Run ESLint
      working-directory: ./app
      run: npm run lint

    - name: Run type check
      working-directory: ./app
      run: npm run type-check

    - name: Run unit tests
      working-directory: ./app
      run: npm run test:unit -- --coverage --watchAll=false

    - name: Build application
      working-directory: ./app
      run: npm run build

  e2e-test:
    runs-on: ubuntu-latest
    needs: [test, frontend-test]

    steps:
    - uses: actions/checkout@v3

    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        cd app && npm ci

    - name: Start application
      run: |
        cd backend && python main.py &
        cd ../app && npm run dev &
        sleep 30  # 等待应用启动

    - name: Install Playwright
      run: |
        npx playwright install --with-deps

    - name: Run E2E tests
      run: |
        npx playwright test

    - name: Upload test results
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: playwright-report
        path: playwright-report/
```

---

## 10. 常见问题与解决方案

### 10.1 开发环境问题

#### Q: 数据库连接失败
**A: 检查以下配置**
```bash
# 1. 检查环境变量
echo $DATABASE_URL

# 2. 测试数据库连接
psql $DATABASE_URL -c "SELECT 1"

# 3. 检查数据库是否运行
docker ps | grep postgres

# 4. 查看数据库日志
docker logs postgres-container
```

#### Q: 前端构建失败
**A: 常见解决方案**
```bash
# 1. 清除缓存
rm -rf .next node_modules
npm install

# 2. 检查TypeScript错误
npm run type-check

# 3. 检查环境变量
cat .env.local

# 4. 检查依赖冲突
npm ls
```

#### Q: API请求403权限错误
**A: 权限检查流程**
```python
# 1. 检查用户角色
SELECT role FROM users WHERE email = 'your-email@example.com';

# 2. 检查权限矩阵
SELECT * FROM permission_matrix WHERE role = 'your-role';

# 3. 检查RLS策略
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual
FROM pg_policies
WHERE tablename IN ('projects', 'ad_accounts');
```

### 10.2 业务逻辑问题

#### Q: 充值流程卡在数据员审批
**A: 检查点和解决方案**
```sql
-- 1. 检查充值申请状态
SELECT id, status, clerk_approval, finance_approval
FROM topups
WHERE status = 'pending';

-- 2. 检查数据员权限
SELECT id, email, role FROM users WHERE role = 'data_clerk';

-- 3. 检查审批历史
SELECT * FROM audit_logs
WHERE table_name = 'topups'
AND action = 'update'
ORDER BY created_at DESC;
```

```python
# 4. 重新发送审批通知
async def resend_approval_notification(topup_id: str):
    topup = db.query(Topup).filter(Topup.id == topup_id).first()
    if topup and topup.status == "pending":
        await notify_data_clerk_for_approval(topup)
        return True
    return False
```

#### Q: 对账差异过大
**A: 差异分析和处理**
```python
# 1. 详细差异分析
async def detailed_variance_analysis(project_id: str, start_date: datetime, end_date: datetime):

    # 检查时间差异
    time_diff_topups = db.query(Topup).filter(
        Topup.project_id == project_id,
        Topup.completed_at.between(start_date, end_date + timedelta(days=7))
    ).all()

    # 检查手续费差异
    fee_analysis = db.query(
        func.sum(Topup.fee_amount),
        func.avg(Topup.fee_rate)
    ).filter(
        Topup.project_id == project_id,
        Topup.completed_at.between(start_date, end_date)
    ).first()

    # 检查异常交易
    suspicious_transactions = db.query(Topup).filter(
        Topup.project_id == project_id,
        Topup.completed_at.between(start_date, end_date),
        Topup.amount > 10000  # 大额交易
    ).all()

    return {
        "time_delay_topups": len(time_diff_topups),
        "total_fees": float(fee_analysis[0] or 0),
        "avg_fee_rate": float(fee_analysis[1] or 0),
        "suspicious_transactions": len(suspicious_transactions)
    }
```

### 10.3 性能优化问题

#### Q: API响应缓慢
**A: 性能优化检查**
```sql
-- 1. 检查慢查询
SELECT query, mean_time, calls, total_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- 2. 检查缺失的索引
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE schemaname = 'public'
AND tablename IN ('projects', 'ad_accounts', 'ad_spend_daily');

-- 3. 检查数据库连接
SELECT state, count(*)
FROM pg_stat_activity
GROUP BY state;
```

```python
# 4. API响应时间优化
from functools import lru_cache
import asyncio

class OptimizedProjectService:

    @lru_cache(maxsize=128)
    def get_project_cached(self, project_id: str):
        """缓存项目信息"""
        return db.query(Project).filter(Project.id == project_id).first()

    async def get_projects_batch(self, project_ids: List[str]):
        """批量获取项目信息"""
        projects = db.query(Project).filter(Project.id.in_(project_ids)).all()
        return {p.id: p for p in projects}

    async def get_project_stats_async(self, project_id: str):
        """异步获取项目统计"""
        tasks = [
            asyncio.create_task(self.get_total_spend(project_id)),
            asyncio.create_task(self.get_total_leads(project_id)),
            asyncio.create_task(self.get_account_count(project_id))
        ]

        spend, leads, account_count = await asyncio.gather(*tasks)
        return {
            "total_spend": spend,
            "total_leads": leads,
            "account_count": account_count
        }
```

### 10.4 安全问题

#### Q: 发现安全漏洞
**A: 安全应急响应**
```python
# 1. 立即禁用受影响账户
async def emergency_disable_account(user_id: str):
    """紧急禁用用户账户"""
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.is_active = False
        # 将所有JWT token加入黑名单
        await jwt_manager.blacklist_all_user_tokens(user_id)

        # 记录安全事件
        security_logger.log_security_event(
            event_type="account_disabled_emergency",
            severity="critical",
            user_id=user_id,
            details={"reason": "security_vulnerability"}
        )

        db.commit()

# 2. 检查异常活动
async def check_suspicious_activity(user_id: str):
    """检查可疑活动"""
    recent_logs = db.query(AuditLog).filter(
        AuditLog.user_id == user_id,
        AuditLog.created_at >= datetime.utcnow() - timedelta(hours=24)
    ).all()

    # 检查异常模式
    suspicious_patterns = []
    for log in recent_logs:
        if log.action in ["delete", "export"]:
            suspicious_patterns.append({
                "action": log.action,
                "timestamp": log.created_at,
                "ip_address": log.ip_address
            })

    return suspicious_patterns
```

#### Q: 数据泄露应急处理
**A: 数据保护措施**
```bash
# 1. 立即更改数据库密码
ALTER USER postgres PASSWORD 'new_strong_password';

# 2. 检查数据访问日志
SELECT user_id, action, table_name, created_at
FROM audit_logs
WHERE created_at >= NOW() - INTERVAL '24 hours'
AND table_name IN ('projects', 'ad_accounts', 'users')
ORDER BY created_at DESC;

# 3. 备份关键数据
pg_dump -h localhost -U postgres -d ad_spend \
    --format=custom \
    --file=emergency_backup_$(date +%Y%m%d_%H%M%S).dump

# 4. 启用额外审计
ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_min_duration_statement = 0;
SELECT pg_reload_conf();
```

### 10.5 运维问题

#### Q: 服务器宕机恢复
**A: 灾难恢复流程**
```bash
#!/bin/bash
# disaster_recovery.sh

echo "开始灾难恢复流程..."

# 1. 检查系统状态
systemctl status nginx
systemctl status postgresql
systemctl status redis

# 2. 从备份恢复数据库
if [ -f "/backups/latest_backup.dump" ]; then
    echo "恢复数据库..."
    pg_restore -h localhost -U postgres -d ad_spend \
        --clean --if-exists --verbose /backups/latest_backup.dump
else
    echo "未找到备份文件!"
    exit 1
fi

# 3. 恢复文件
echo "恢复文件..."
tar -xzf /backups/files_backup_latest.tar.gz -C /

# 4. 重启服务
echo "重启服务..."
systemctl restart postgresql
systemctl restart redis
systemctl restart nginx

# 5. 验证服务
curl -f http://localhost:8000/health || exit 1
curl -f http://localhost:3000 || exit 1

echo "灾难恢复完成!"
```

#### Q: 数据库性能下降
**A: 性能诊断和优化**
```sql
-- 1. 检查数据库统计信息
SELECT schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del, n_live_tup, n_dead_tup
FROM pg_stat_user_tables
ORDER BY n_dead_tup DESC;

-- 2. 更新统计信息
ANALYZE;

-- 3. 重建索引
REINDEX DATABASE ad_spend;

-- 4. 清理死元组
VACUUM (VERBOSE, ANALYZE) ad_accounts;
VACUUM (VERBOSE, ANALYZE) ad_spend_daily;

-- 5. 检查锁等待
SELECT blocked_locks.pid AS blocked_pid,
       blocked_activity.usename AS blocked_user,
       blocking_locks.pid AS blocking_pid,
       blocking_activity.usename AS blocking_user,
       blocked_activity.query AS blocked_statement,
       blocking_activity.query AS current_statement_in_blocking_process
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;
```

---

## 📞 技术支持

### 开发团队联系方式
- **技术负责人**: [待填写]
- **架构师**: [待填写]
- **前端负责人**: [待填写]
- **后端负责人**: [待填写]
- **运维负责人**: [待填写]

### 紧急联系
- **系统故障**: 立即联系技术负责人
- **安全事件**: 立即联系安全团队
- **数据问题**: 联系DBA团队

---

**文档版本**: v1.0
**最后更新**: 2025-11-10
**下次审查**: 功能变更时