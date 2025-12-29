# AI广告代投系统 - SQLAlchemy 模型层

## 📋 概述

本目录包含 AI广告代投系统的完整 SQLAlchemy ORM 模型定义，严格对齐数据库初始化脚本 `backend/scripts/init_db_schema.py` v2.3。

## 📁 文件结构

```
backend/models/
├── base.py                 # SQLAlchemy 基类和 Mixin
├── __init__.py            # 统一导出所有模型
├── README.md              # 本文件 - 使用说明
└── [legacy files]         # 旧版模型文件（逐步废弃）
```

## 🗂️ 数据库表清单

### 基础表 (3张)
- `users` - 系统用户表
- `channels` - 广告渠道表
- `projects` - 项目表

### 账户管理表 (4张)
- `channel_reviews` - 渠道评审记录表
- `channel_account_requests` - 渠道开户申请记录表
- `ad_accounts` - 广告账户表（核心）
- `channel_performance` - 渠道表现统计表

### 业务流程表 (3张)
- `daily_reports` - 投手每日报告表
- `topup_requests` - 充值申请表
- `ad_spend_daily` - 每日广告花费数据表

### 财务表 (3张)
- `ledger_entries` - 总账分录表
- `reconciliation_batches` - 对账批次表
- `reconciliation_details` - 对账明细表

### 系统支持表 (3张)
- `audit_logs` - 审计日志表
- `account_status_history` - 账户状态变更历史表
- `account_alerts` - 账户预警表

## 🚀 快速开始

### 基本导入

```python
# 推荐方式：从 __init__.py 导入
from backend.models import (
    Base,
    User,
    Project,
    AdAccount,
    DailyReport,
    TopupRequest,
    # ... 其他模型
)
```

### 创建数据库会话

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import Base

# 从环境变量读取数据库 URL
import os
DATABASE_URL = os.getenv('DATABASE_URL')

# 创建引擎
engine = create_engine(DATABASE_URL, echo=True)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建所有表（如果不存在）
Base.metadata.create_all(bind=engine)
```

### 基本CRUD操作示例

#### 创建记录

```python
from backend.models import User, Project, AdAccount
from sqlalchemy.orm import Session

def create_user(db: Session):
    """创建用户"""
    user = User(
        username="john_doe",
        email="john@example.com",
        hashed_password="hashed_password_here",
        role="media_buyer",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def create_project(db: Session, created_by_id: UUID):
    """创建项目"""
    project = Project(
        project_name="测试项目",
        project_code="TEST001",
        client_name="测试客户",
        status="draft",
        created_by=created_by_id
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project
```

#### 查询记录

```python
from backend.models import User, AdAccount
from sqlalchemy.orm import Session

def get_user_by_username(db: Session, username: str):
    """根据用户名查询用户"""
    return db.query(User).filter(User.username == username).first()

def get_active_ad_accounts(db: Session, project_id: int):
    """查询项目下的活跃广告账户"""
    return db.query(AdAccount).filter(
        AdAccount.project_id == project_id,
        AdAccount.status == 'active'
    ).all()

def get_user_projects(db: Session, user_id: UUID):
    """查询用户创建的项目"""
    return db.query(Project).filter(
        Project.created_by == user_id
    ).all()
```

#### 更新记录

```python
from backend.models import AdAccount
from sqlalchemy.orm import Session

def update_account_balance(db: Session, account_id: int, new_balance: Decimal):
    """更新账户余额"""
    account = db.query(AdAccount).filter(AdAccount.id == account_id).first()
    if account:
        account.balance = new_balance
        db.commit()
        db.refresh(account)
    return account

def suspend_account(db: Session, account_id: int, reason: str):
    """暂停账户"""
    account = db.query(AdAccount).filter(AdAccount.id == account_id).first()
    if account:
        account.status = 'suspended'
        account.notes = reason
        db.commit()
        db.refresh(account)
    return account
```

#### 删除记录

```python
from backend.models import DailyReport
from sqlalchemy.orm import Session

def delete_daily_report(db: Session, report_id: int):
    """删除日报"""
    report = db.query(DailyReport).filter(DailyReport.id == report_id).first()
    if report:
        db.delete(report)
        db.commit()
        return True
    return False
```

## 🔍 高级查询示例

### 关联查询

```python
from backend.models import Project, AdAccount, User
from sqlalchemy.orm import Session, joinedload

def get_project_with_accounts(db: Session, project_id: int):
    """查询项目及其所有广告账户"""
    return db.query(Project).filter(
        Project.id == project_id
    ).options(joinedload(Project.ad_accounts)).first()

def get_account_with_details(db: Session, account_id: int):
    """查询账户及关联的项目、渠道、负责人信息"""
    return db.query(AdAccount).filter(
        AdAccount.id == account_id
    ).options(
        joinedload(AdAccount.project),
        joinedload(AdAccount.channel),
        joinedload(AdAccount.assigned_to)
    ).first()
```

### 聚合查询

```python
from backend.models import AdAccount, LedgerEntry
from sqlalchemy import func
from sqlalchemy.orm import Session

def get_account_statistics(db: Session, project_id: int):
    """统计项目下账户信息"""
    return db.query(
        func.count(AdAccount.id).label('total_accounts'),
        func.count(AdAccount.id).filter(AdAccount.status == 'active').label('active_accounts'),
        func.sum(AdAccount.balance).label('total_balance')
    ).filter(AdAccount.project_id == project_id).first()

def get_total_spend_by_account(db: Session, account_id: int):
    """计算账户总消耗"""
    return db.query(
        func.sum(LedgerEntry.amount)
    ).filter(
        LedgerEntry.ad_account_id == account_id,
        LedgerEntry.entry_type == 'spend'
    ).scalar()
```

### 分页查询

```python
from backend.models import DailyReport
from sqlalchemy.orm import Session

def get_reports_paginated(db: Session, page: int = 1, page_size: int = 20):
    """分页查询日报"""
    offset = (page - 1) * page_size

    total = db.query(DailyReport).count()
    reports = db.query(DailyReport)\
        .order_by(DailyReport.report_date.desc())\
        .offset(offset)\
        .limit(page_size)\
        .all()

    return {
        'total': total,
        'page': page,
        'page_size': page_size,
        'data': reports
    }
```

## ⚠️ 重要约束

### 状态字段枚举值

所有状态字段必须使用数据库 CHECK 约束中定义的合法值（参考 `STATE_MACHINE.md`）：

```python
# channels.status
CHANNEL_STATUS = ['active', 'inactive']

# projects.status
PROJECT_STATUS = ['draft', 'active', 'suspended', 'archived']

# ad_accounts.status
ACCOUNT_STATUS = ['new', 'testing', 'active', 'suspended', 'dead', 'archived']

# daily_reports.status
REPORT_STATUS = ['draft', 'pending', 'approved', 'rejected']

# topup_requests.status
TOPUP_STATUS = ['draft', 'pending_review', 'finance_approve', 'paid', 'completed', 'rejected', 'cancelled']

# reconciliation_batches.status
BATCH_STATUS = ['draft', 'pending', 'reviewing', 'closed']

# reconciliation_details.status
DETAIL_STATUS = ['pending', 'confirmed', 'adjusted']

# account_alerts.status
ALERT_STATUS = ['open', 'ack', 'resolved']

# ledger_entries.entry_type
ENTRY_TYPE = ['topup_received', 'spend', 'adjustment']
```

### 唯一约束

以下字段组合必须唯一：

- `users.username`
- `users.email`
- `channels.channel_code`
- `projects.project_code`
- `ad_accounts.account_code`
- `daily_reports.(ad_account_id, report_date)`
- `ad_spend_daily.(ad_account_code, spend_date)`
- `reconciliation_batches.batch_code`
- `channel_performance.(channel_id, stat_date)`

### 外键级联删除规则

- **CASCADE**: 删除父记录时自动删除子记录
  - `projects` → `ad_accounts`
  - `ad_accounts` → `daily_reports`, `topup_requests`, `ledger_entries`, `account_alerts`
  - `reconciliation_batches` → `reconciliation_details`

- **RESTRICT**: 禁止删除有关联记录的父记录
  - `users` → `audit_logs`
  - `ad_accounts` → `account_status_history`

- **SET NULL**: 删除父记录时将外键设置为 NULL
  - `users` → `projects.created_by`, `ad_accounts.assigned_to`, 等

## 📊 数据类型说明

- **UUID**: 用于用户 ID（`users.id`）
- **BIGSERIAL**: 用于业务表主键（自增）
- **NUMERIC(15,2)**: 用于金额字段（支持最大 999,999,999,999.99）
- **NUMERIC(12,4)**: 用于比率字段（如 ROI）
- **TIMESTAMPTZ**: 带时区的时间戳
- **DATE**: 日期字段
- **JSONB**: JSON 数据（metadata, old_values, new_values 等）

## 🔧 迁移管理

建议使用 Alembic 进行数据库迁移管理：

```bash
# 安装 Alembic
pip install alembic

# 初始化 Alembic
alembic init alembic

# 创建迁移脚本
alembic revision --autogenerate -m "Initial migration"

# 执行迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

## 📚 参考文档

- **数据库架构**: `backend/scripts/init_db_schema.py` v2.3
- **数据Schema**: `docs/core/DATA_SCHEMA.md` v5.0
- **状态机定义**: `docs/core/STATE_MACHINE.md` v2.3
- **API开发流程**: `docs/core/API_DEVELOPMENT_FLOW.md`

## ⚡ 性能优化建议

1. **使用索引**: 模型中已定义所有必要的索引，确保数据库中已创建
2. **查询优化**: 使用 `joinedload()` 或 `selectinload()` 避免 N+1 查询问题
3. **分页查询**: 对于大数据集使用 `limit()` 和 `offset()`
4. **批量操作**: 使用 `bulk_insert_mappings()` 或 `bulk_update_mappings()`
5. **连接池**: 配置适当的数据库连接池大小

## 🆘 常见问题

### Q: 如何处理时区？

A: 所有 DateTime 字段使用 `DateTime(timezone=True)` 类型，自动处理时区转换。

### Q: 如何实现软删除？

A: 当前模型使用硬删除。如需软删除，可添加 `is_deleted` 字段并修改查询逻辑。

### Q: 如何记录审计日志？

A: 使用 `AuditLog` 模型记录所有敏感操作，包含操作前后的值。

### Q: 模型与数据库不一致怎么办？

A: 使用 Alembic 生成迁移脚本，或重新运行 `init_db_schema.py` 初始化数据库。

---

**版本**: v2.3
**最后更新**: 2025-11-19
**维护者**: 数据库架构团队
