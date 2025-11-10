# 状态机定义与业务流程

> **文档目的**: 定义系统核心业务流程的状态转换规则和权限控制
> **目标读者**: 业务分析师、后端开发工程师、产品经理
> **更新日期**: 2025-11-10

---

## 1. 状态机设计原则

### 1.1 核心设计理念
- **状态明确**: 每个状态都有明确的业务含义
- **转换合法**: 状态转换必须符合业务规则
- **权限控制**: 不同角色只能执行特定状态转换
- **可追溯**: 所有状态变更都有完整记录
- **不可逆**: 重要业务流程不允许随意回退

### 1.2 状态转换规则
```sql
-- 状态转换表定义
CREATE TABLE state_transitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(50) NOT NULL,          -- 实体类型
    current_state VARCHAR(50) NOT NULL,        -- 当前状态
    next_state VARCHAR(50) NOT NULL,           -- 目标状态
    allowed_roles TEXT[] NOT NULL,             -- 允许的角色
    required_conditions JSONB,                  -- 必要条件
    auto_transition BOOLEAN DEFAULT false,       -- 是否自动转换
    action_type VARCHAR(50),                    -- 触发动作类型
    description TEXT,                             -- 转换描述
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 1.3 通用状态机基类
```python
# core/state_machine.py
from enum import Enum
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class State(Enum):
    """状态枚举基类"""
    pass

class StateTransition:
    """状态转换定义"""
    def __init__(
        self,
        from_state: State,
        to_state: State,
        allowed_roles: List[str],
        conditions: Optional[List[Callable]] = None,
        action: Optional[Callable] = None,
        auto: bool = False,
        description: str = ""
    ):
        self.from_state = from_state
        self.to_state = to_state
        self.allowed_roles = allowed_roles
        self.conditions = conditions or []
        self.action = action
        self.auto = auto
        self.description = description

class BaseStateMachine:
    """状态机基类"""

    def __init__(self, initial_state: State):
        self.current_state = initial_state
        self.transitions: Dict[State, List[StateTransition]] = {}
        self.history: List[Dict] = []

    def add_transition(self, transition: StateTransition):
        """添加状态转换"""
        if transition.from_state not in self.transitions:
            self.transitions[transition.from_state] = []
        self.transitions[transition.from_state].append(transition)

    def can_transition(self, to_state: State, user_role: str, context: Dict = None) -> bool:
        """检查是否可以转换到目标状态"""
        if self.current_state not in self.transitions:
            return False

        for transition in self.transitions[self.current_state]:
            if transition.to_state == to_state and user_role in transition.allowed_roles:
                # 检查条件
                if transition.conditions:
                    for condition in transition.conditions:
                        if not condition(context or {}):
                            return False
                return True

        return False

    async def transition(
        self,
        to_state: State,
        user_id: str,
        user_role: str,
        reason: str = None,
        context: Dict = None
    ) -> Dict:
        """执行状态转换"""
        context = context or {}

        if not self.can_transition(to_state, user_role, context):
            raise ValueError(
                f"无法从 {self.current_state.value} 转换到 {to_state.value}，"
                f"用户角色: {user_role}，条件检查失败"
            )

        # 执行转换前的动作
        transition = self._find_transition(to_state, user_role)
        old_state = self.current_state

        # 执行条件检查
        if transition.conditions:
            for condition in transition.conditions:
                if not condition(context):
                    raise ValueError(f"状态转换条件检查失败: {condition.__name__}")

        # 执行业务动作
        if transition.action:
            action_result = await transition.action(context)
            context.update(action_result or {})

        # 更新状态
        self.current_state = to_state

        # 记录历史
        history_entry = {
            "from_state": old_state.value,
            "to_state": to_state.value,
            "user_id": user_id,
            "user_role": user_role,
            "reason": reason,
            "context": context,
            "timestamp": datetime.utcnow().isoformat(),
            "auto": transition.auto
        }

        self.history.append(history_entry)

        logger.info(
            f"状态转换: {old_state.value} -> {to_state.value}, "
            f"用户: {user_id}, 角色: {user_role}, 原因: {reason}"
        )

        return {
            "success": True,
            "old_state": old_state.value,
            "new_state": to_state.value,
            "transition_id": len(self.history),
            "timestamp": history_entry["timestamp"]
        }

    def _find_transition(self, to_state: State, user_role: str) -> StateTransition:
        """查找状态转换"""
        for transition in self.transitions[self.current_state]:
            if transition.to_state == to_state and user_role in transition.allowed_roles:
                return transition
        raise ValueError(f"未找到有效的状态转换: {self.current_state.value} -> {to_state.value}")

    def get_available_transitions(self, user_role: str) -> List[State]:
        """获取用户角色可用的状态转换"""
        if self.current_state not in self.transitions:
            return []

        available_states = []
        for transition in self.transitions[self.current_state]:
            if user_role in transition.allowed_roles:
                available_states.append(transition.to_state)

        return available_states

    def get_current_state(self) -> State:
        """获取当前状态"""
        return self.current_state

    def get_transition_history(self, limit: int = None) -> List[Dict]:
        """获取转换历史"""
        if limit:
            return self.history[-limit:] if len(self.history) > limit else self.history
        return self.history
```

---

## 2. 充值申请状态机

### 2.1 状态定义
```python
# models/topup_states.py
from enum import Enum

class TopupStatus(str, Enum):
    """充值申请状态"""
    DRAFT = "draft"              # 草稿
    PENDING = "pending"            # 待审核
    CLERK_APPROVED = "clerk_approved"  # 数据员批准
    FINANCE_APPROVED = "finance_approved"  # 财务批准
    PAID = "paid"                 # 已付款
    POSTED = "posted"              # 已记账
    REJECTED = "rejected"           # 已拒绝
    CANCELLED = "cancelled"         # 已取消
```

### 2.2 状态转换规则
```python
# services/topup_state_machine.py
from backend.core.state_machine import BaseStateMachine, StateTransition
from backend.models.topup_states import TopupStatus
from backend.services.notification_service import notification_service
from backend.core.audit import audit_logger

class TopupStateMachine(BaseStateMachine):
    """充值申请状态机"""

    def __init__(self, initial_state: TopupStatus = TopupStatus.DRAFT):
        super().__init__(initial_state)
        self._setup_transitions()

    def _setup_transitions(self):
        """设置状态转换规则"""

        # 投手提交申请
        self.add_transition(StateTransition(
            from_state=TopupStatus.DRAFT,
            to_state=TopupStatus.PENDING,
            allowed_roles=["media_buyer", "admin", "manager"],
            conditions=[self._validate_submission],
            action=self._on_submit,
            description="投手提交充值申请"
        ))

        # 数据员审批
        self.add_transition(StateTransition(
            from_state=TopupStatus.PENDING,
            to_state=TopupStatus.CLERK_APPROVED,
            allowed_roles=["data_clerk", "admin"],
            conditions=[self._validate_clerk_approval],
            action=self._on_clerk_approve,
            description="数据员批准充值申请"
        ))

        # 数据员拒绝
        self.add_transition(StateTransition(
            from_state=TopupStatus.PENDING,
            to_state=TopupStatus.REJECTED,
            allowed_roles=["data_clerk", "admin"],
            conditions=[self._validate_rejection],
            action=self._on_reject,
            description="数据员拒绝充值申请"
        ))

        # 财务审批
        self.add_transition(StateTransition(
            from_state=TopupStatus.CLERK_APPROVED,
            to_state=TopupStatus.FINANCE_APPROVED,
            allowed_roles=["finance", "admin"],
            conditions=[self._validate_finance_approval],
            action=self._on_finance_approve,
            description="财务批准充值申请"
        ))

        # 财务拒绝
        self.add_transition(StateTransition(
            from_state=TopupStatus.CLERK_APPROVED,
            to_state=TopupStatus.REJECTED,
            allowed_roles=["finance", "admin"],
            conditions=[self._validate_rejection],
            action=self._on_reject,
            description="财务拒绝充值申请"
        ))

        # 财务付款
        self.add_transition(StateTransition(
            from_state=TopupStatus.FINANCE_APPROVED,
            to_state=TopupStatus.PAID,
            allowed_roles=["finance", "admin"],
            conditions=[self._validate_payment],
            action=self._on_pay,
            description="财务执行付款"
        ))

        # 系统自动记账
        self.add_transition(StateTransition(
            from_state=TopupStatus.PAID,
            to_state=TopupStatus.POSTED,
            allowed_roles=["system"],
            auto=True,
            action=self._on_post,
            description="系统自动记账"
        ))

        # 重新提交（被拒绝后）
        self.add_transition(StateTransition(
            from_state=TopupStatus.REJECTED,
            to_state=TopupStatus.DRAFT,
            allowed_roles=["media_buyer", "admin", "manager"],
            conditions=[self._validate_resubmission],
            action=self._on_resubmit,
            description="重新提交充值申请"
        ))

        # 取消申请
        self.add_transition(StateTransition(
            from_state=TopupStatus.DRAFT,
            to_state=TopupStatus.CANCELLED,
            allowed_roles=["media_buyer", "admin", "manager"],
            action=self._on_cancel,
            description="取消充值申请"
        ))

    def _validate_submission(self, context: Dict) -> bool:
        """验证提交申请"""
        required_fields = ["amount", "ad_account_id", "purpose"]
        for field in required_fields:
            if field not in context or not context[field]:
                raise ValueError(f"缺少必填字段: {field}")

        if context["amount"] <= 0:
            raise ValueError("充值金额必须大于0")

        if context["amount"] < 100:
            raise ValueError("充值金额不能小于100")

        return True

    def _validate_clerk_approval(self, context: Dict) -> bool:
        """验证数据员审批"""
        # 检查账户余额合理性
        if "account_balance" in context:
            if context["account_balance"] > 1000 and context["amount"] < 1000:
                raise ValueError("账户余额充足，暂不需要充值")

        # 检查充值频率
        if "recent_topups_count" in context:
            if context["recent_topups_count"] >= 3:  # 最近7天超过3次
                raise ValueError("充值频率过高，请先消耗现有余额")

        return True

    def _validate_finance_approval(self, context: Dict) -> bool:
        """验证财务审批"""
        if "payment_method" not in context:
            raise ValueError("必须指定付款方式")

        if context["amount"] > 50000:  # 大额充值需要额外审批
            if "high_level_approval" not in context:
                raise ValueError("超过5万元的充值需要高级别审批")

        return True

    def _validate_payment(self, context: Dict) -> bool:
        """验证付款"""
        if "transaction_id" not in context:
            raise ValueError("缺少交易ID")

        if "payment_method" not in context:
            raise ValueError("缺少付款方式")

        return True

    def _validate_rejection(self, context: Dict) -> bool:
        """验证拒绝"""
        if "reason" not in context or not context["reason"].strip():
            raise ValueError("拒绝时必须提供原因")

        return True

    def _validate_resubmission(self, context: Dict) -> bool:
        """验证重新提交"""
        # 检查是否修改了被拒绝的问题
        if "rejection_reason" in context:
            common_issues = ["金额过大", "缺少用途说明", "账户余额充足", "充值频率过高"]
            for issue in common_issues:
                if issue in context["rejection_reason"]:
                    raise ValueError(f"请先解决被拒绝的问题: {issue}")

        return True

    async def _on_submit(self, context: Dict) -> Dict:
        """提交申请时的动作"""
        # 发送通知给数据员
        await notification_service.send_topup_request_notification(context["topup_id"])

        # 记录审计日志
        await audit_logger.log_action(
            action="topup_submit",
            table_name="topups",
            record_id=context["topup_id"],
            user_id=context["user_id"],
            details={"amount": context["amount"], "purpose": context["purpose"]}
        )

        return {"notification_sent": True}

    async def _on_clerk_approve(self, context: Dict) -> Dict:
        """数据员批准时的动作"""
        # 记录审批信息
        await audit_logger.log_action(
            action="topup_clerk_approve",
            table_name="topups",
            record_id=context["topup_id"],
            user_id=context["user_id"],
            details={"amount": context["amount"], "notes": context.get("notes", "")}
        )

        # 发送通知给财务
        await notification_service.send_finance_approval_notification(context["topup_id"])

        return {"notified_finance": True}

    async def _on_finance_approve(self, context: Dict) -> Dict:
        """财务批准时的动作"""
        # 预留付款
        await self._reserve_payment(context["topup_id"], context["amount"])

        # 记录审批信息
        await audit_logger.log_action(
            action="topup_finance_approve",
            table_name="topups",
            record_id=context["topup_id"],
            user_id=context["user_id"],
            details={"amount": context["amount"], "payment_method": context["payment_method"]}
        )

        return {"payment_reserved": True}

    async def _on_pay(self, context: Dict) -> Dict:
        """付款时的动作"""
        # 执行付款
        await self._execute_payment(
            context["topup_id"],
            context["transaction_id"],
            context["payment_method"]
        )

        # 记录付款信息
        await audit_logger.log_action(
            action="topup_payment",
            table_name="topups",
            record_id=context["topup_id"],
            user_id=context["user_id"],
            details={"transaction_id": context["transaction_id"], "amount": context["amount"]}
        )

        return {"payment_executed": True}

    async def _on_post(self, context: Dict) -> Dict:
        """记账时的动作"""
        # 更新账户余额
        await self._update_account_balance(context["topup_id"])

        # 创建财务流水
        await self._create_financial_transaction(context["topup_id"])

        # 更新相关统计
        await self._update_project_statistics(context["project_id"])

        # 发送完成通知
        await notification_service.send_topup_completion_notification(context["topup_id"])

        return {"account_updated": True}

    async def _on_reject(self, context: Dict) -> Dict:
        """拒绝时的动作"""
        # 发送拒绝通知
        await notification_service.send_topup_rejection_notification(
            context["topup_id"],
            context["reason"]
        )

        # 记录拒绝信息
        await audit_logger.log_action(
            action="topup_reject",
            table_name="topups",
            record_id=context["topup_id"],
            user_id=context["user_id"],
            details={"reason": context["reason"]}
        )

        return {"rejection_notified": True}

    async def _on_resubmit(self, context: Dict) -> Dict:
        """重新提交时的动作"""
        # 清除之前的审批记录
        await self._clear_approval_history(context["topup_id"])

        # 记录重新提交
        await audit_logger.log_action(
            action="topup_resubmit",
            table_name="topups",
            record_id=context["topup_id"],
            user_id=context["user_id"],
            details={"resubmission_count": context.get("resubmission_count", 1)}
        )

        return {"approval_cleared": True}

    async def _on_cancel(self, context: Dict) -> Dict:
        """取消时的动作"""
        # 记录取消信息
        await audit_logger.log_action(
            action="topup_cancel",
            table_name="topups",
            record_id=context["topup_id"],
            user_id=context["user_id"],
            details={"reason": context.get("reason", "用户取消")}
        )

        return {"cancelled": True}

    # 私有方法
    async def _reserve_payment(self, topup_id: str, amount: float):
        """预留付款"""
        # 实现预留付款逻辑
        pass

    async def _execute_payment(self, topup_id: str, transaction_id: str, payment_method: str):
        """执行付款"""
        # 实现付款执行逻辑
        pass

    async def _update_account_balance(self, topup_id: str):
        """更新账户余额"""
        # 实现余额更新逻辑
        pass

    async def _create_financial_transaction(self, topup_id: str):
        """创建财务流水"""
        # 实现财务流水创建逻辑
        pass

    async def _update_project_statistics(self, project_id: str):
        """更新项目统计"""
        # 实现统计更新逻辑
        pass

    async def _clear_approval_history(self, topup_id: str):
        """清除审批历史"""
        # 实现审批历史清除逻辑
        pass
```

### 2.3 状态转换表数据
```sql
-- 充值状态转换记录
INSERT INTO state_transitions (entity_type, current_state, next_state, allowed_roles, required_conditions, auto_transition, action_type, description) VALUES
-- 投手提交
('topup', 'draft', 'pending', ARRAY['media_buyer', 'admin', 'manager'],
 '[{"field": "amount", "operator": ">", "value": 0}, {"field": "amount", "operator": ">=", "value": 100}]',
false, 'manual_submit', '投手提交充值申请'),

-- 数据员批准
('topup', 'pending', 'clerk_approved', ARRAY['data_clerk', 'admin'],
'[{"field": "account_balance", "operator": "check_sufficient"}, {"field": "recent_topups_count", "operator": "<", "value": 3}]',
false, 'clerk_approve', '数据员批准充值申请'),

-- 数据员拒绝
('topup', 'pending', 'rejected', ARRAY['data_clerk', 'admin'],
'[{"field": "reason", "operator": "required", "value": true}]',
false, 'clerk_reject', '数据员拒绝充值申请'),

-- 财务批准
('topup', 'clerk_approved', 'finance_approved', ARRAY['finance', 'admin'],
'[{"field": "payment_method", "operator": "required", "value": true}]',
false, 'finance_approve', '财务批准充值申请'),

-- 财务拒绝
('topup', 'clerk_approved', 'rejected', ARRAY['finance', 'admin'],
'[{"field": "reason", "operator": "required", "value": true}]',
false, 'finance_reject', '财务拒绝充值申请'),

-- 财务付款
('topup', 'finance_approved', 'paid', ARRAY['finance', 'admin'],
'[{"field": "transaction_id", "operator": "required", "value": true}, {"field": "payment_method", "operator": "required", "value": true}]',
false, 'finance_pay', '财务执行付款'),

-- 系统记账
('topup', 'paid', 'posted', ARRAY['system'],
'[]',
true, 'system_post', '系统自动记账'),

-- 重新提交
('topup', 'rejected', 'draft', ARRAY['media_buyer', 'admin', 'manager'],
'[{"field": "rejection_reason", "operator": "validate_improvement"}]',
false, 'resubmit', '重新提交充值申请'),

-- 取消申请
('topup', 'draft', 'cancelled', ARRAY['media_buyer', 'admin', 'manager'],
'[]',
false, 'cancel', '取消充值申请');
```

---

## 3. 日报状态机

### 3.1 状态定义
```python
# models/daily_report_states.py
class DailyReportStatus(str, Enum):
    """日报状态"""
    DRAFT = "draft"        # 草稿
    PENDING = "pending"      # 待审核
    APPROVED = "approved"    # 已审核
    REJECTED = "rejected"    # 已拒绝
```

### 3.2 状态转换规则
```python
# services/daily_report_state_machine.py
class DailyReportStateMachine(BaseStateMachine):
    """日报状态机"""

    def __init__(self, initial_state: DailyReportStatus = DailyReportStatus.DRAFT):
        super().__init__(initial_state)
        self._setup_transitions()

    def _setup_transitions(self):
        """设置状态转换规则"""

        # 投手提交日报
        self.add_transition(StateTransition(
            from_state=DailyReportStatus.DRAFT,
            to_state=DailyReportStatus.PENDING,
            allowed_roles=["media_buyer", "admin", "manager"],
            conditions=[self._validate_submission],
            action=self._on_submit,
            description="投手提交日报"
        ))

        # 数据员确认
        self.add_transition(StateTransition(
            from_state=DailyReportStatus.PENDING,
            to_state=DailyReportStatus.APPROVED,
            allowed_roles=["data_clerk", "admin"],
            conditions=[self._validate_confirmation],
            action=self._on_approve,
            description="数据员确认日报"
        ))

        # 数据员拒绝
        self.add_transition(StateTransition(
            from_state=DailyReportStatus.PENDING,
            to_state=DailyReportStatus.REJECTED,
            allowed_roles=["data_clerk", "admin"],
            conditions=[self._validate_rejection],
            action=self._on_reject,
            description="数据员拒绝日报"
        ))

        # 重新提交（被拒绝后）
        self.add_transition(StateTransition(
            from_state=DailyReportStatus.REJECTED,
            to_state=DailyReportStatus.DRAFT,
            allowed_roles=["media_buyer", "admin", "manager"],
            action=self._on_resubmit,
            description="重新提交日报"
        ))

    def _validate_submission(self, context: Dict) -> bool:
        """验证日报提交"""
        required_fields = ["date", "spend", "leads_submitted", "ad_account_id"]
        for field in required_fields:
            if field not in context or context[field] is None:
                raise ValueError(f"缺少必填字段: {field}")

        # 检查是否重复提交
        if await self._check_duplicate_submission(
            context["ad_account_id"],
            context["date"]
        ):
            raise ValueError("该日期的日报已存在")

        # 验证消耗数据
        if context["spend"] < 0:
            raise ValueError("消耗金额不能为负数")

        if context["leads_submitted"] < 0:
            raise ValueError("提交的粉数不能为负数")

        # 验证日期合理性
        report_date = context["date"]
        if report_date > datetime.now().date():
            raise ValueError("不能提交未来的日报")

        # 检查账户状态
        account_status = context.get("account_status")
        if account_status in ["suspended", "dead"]:
            raise ValueError(f"账户状态为{account_status}，无法提交日报")

        return True

    def _validate_confirmation(self, context: Dict) -> bool:
        """验证确认"""
        if "leads_confirmed" not in context:
            raise ValueError("必须确认粉数")

        leads_confirmed = context["leads_confirmed"]
        leads_submitted = context.get("leads_submitted", 0)

        if leads_confirmed < 0:
            raise ValueError("确认的粉数不能为负数")

        # 检查粉数合理性
        if leads_submitted > 0:
            diff_ratio = abs(leads_confirmed - leads_submitted) / leads_submitted
            if diff_ratio > 0.5:  # 超过50%差异
                raise ValueError("确认粉数与提交粉数差异过大，请仔细核对")

        return True

    def _validate_rejection(self, context: Dict) -> bool:
        """验证拒绝"""
        if "reason" not in context or not context["reason"].strip():
            raise ValueError("拒绝时必须提供原因")

        return True

    async def _on_submit(self, context: Dict) -> Dict:
        """提交时的动作"""
        # 计算初始指标
        await self._calculate_initial_metrics(context["report_id"])

        # 发送审核通知
        await notification_service.send_daily_report_notification(context["report_id"])

        return {"metrics_calculated": True}

    async def _on_approve(self, context: Dict) -> Dict:
        """批准时的动作"""
        # 更新最终指标
        await self._calculate_final_metrics(
            context["report_id"],
            context["leads_confirmed"]
        )

        # 检查异常
        anomalies = await self._detect_anomalies(context["report_id"])
        if anomalies:
            await self._mark_anomalies(context["report_id"], anomalies)

        return {"final_metrics_updated": True}

    async def _on_reject(self, context: Dict) -> Dict:
        """拒绝时的动作"""
        # 发送拒绝通知
        await notification_service.send_daily_report_rejection_notification(
            context["report_id"],
            context["reason"]
        )

        return {"rejection_notified": True}

    async def _check_duplicate_submission(self, account_id: str, report_date: datetime.date) -> bool:
        """检查重复提交"""
        # 实现重复提交检查逻辑
        pass

    async def _calculate_initial_metrics(self, report_id: str):
        """计算初始指标"""
        # 实现初始指标计算
        pass

    async def _calculate_final_metrics(self, report_id: str, leads_confirmed: int):
        """计算最终指标"""
        # 实现最终指标计算
        pass

    async def _detect_anomalies(self, report_id: str) -> List[Dict]:
        """检测异常"""
        # 实现异常检测逻辑
        return []

    async def _mark_anomalies(self, report_id: str, anomalies: List[Dict]):
        """标记异常"""
        # 实现异常标记逻辑
        pass
```

---

## 4. 广告账户状态机

### 4.1 状态定义
```python
# models/account_states.py
class AccountStatus(str, Enum):
    """账户状态"""
    NEW = "new"           # 新建
    TESTING = "testing"     # 测试期
    ACTIVE = "active"       # 正常投放
    SUSPENDED = "suspended"   # 暂停
    DEAD = "dead"          # 死亡
    ARCHIVED = "archived"    # 已归档
```

### 4.2 状态转换规则
```python
# services/account_state_machine.py
class AccountStateMachine(BaseStateMachine):
    """广告账户状态机"""

    def __init__(self, initial_state: AccountStatus = AccountStatus.NEW):
        super().__init__(initial_state)
        self._setup_transitions()

    def _setup_transitions(self):
        """设置状态转换规则"""

        # 新建到测试期（7天后自动）
        self.add_transition(StateTransition(
            from_state=AccountStatus.NEW,
            to_state=AccountStatus.TESTING,
            allowed_roles=["data_clerk", "admin"],
            auto=True,
            condition=lambda ctx: self._should_enter_testing(ctx),
            action=self._on_enter_testing,
            description="账户进入测试期"
        ))

        # 手动进入测试期
        self.add_transition(StateTransition(
            from_state=AccountStatus.NEW,
            to_state=AccountStatus.TESTING,
            allowed_roles=["data_clerk", "admin"],
            action=self._on_enter_testing_manual,
            description="手动激活测试期"
        ))

        # 测试期到正常投放（满足条件后自动）
        self.add_transition(StateTransition(
            from_state=AccountStatus.TESTING,
            to_state=AccountStatus.ACTIVE,
            allowed_roles=["system", "data_clerk", "admin"],
            auto=True,
            condition=lambda ctx: self._should_become_active(ctx),
            action=self._on_become_active,
            description="账户转为正常投放"
        ))

        # 手动激活
        self.add_transition(StateTransition(
            from_state=AccountStatus.TESTING,
            to_state=AccountStatus.ACTIVE,
            allowed_roles=["data_clerk", "admin"],
            action=self._on_activate_manual,
            description="手动激活账户"
        ))

        # 暂停账户
        self.add_transition(StateTransition(
            from_state=AccountStatus.ACTIVE,
            to_state=AccountStatus.SUSPENDED,
            allowed_roles=["data_clerk", "admin"],
            condition=lambda ctx: self._can_suspend(ctx),
            action=self._on_suspend,
            description="暂停账户投放"
        )

        # 激活暂停的账户
        self.add_transition(StateTransition(
            from_state=AccountStatus.SUSPENDED,
            to_state=AccountStatus.ACTIVE,
            allowed_roles=["data_clerk", "admin"],
            condition=lambda ctx: self._can_resume(ctx),
            action=self._on_resume,
            description="激活暂停的账户"
        )

        # 标记为死亡
        self.add_transition(StateTransition(
            from_state=AccountStatus.ACTIVE,
            to_state=AccountStatus.DEAD,
            allowed_roles=["system", "data_clerk", "admin"],
            auto=True,
            condition=lambda ctx: self._should_mark_as_dead(ctx),
            action=self._on_mark_as_dead,
            description="标记账户为死亡"
        ))

        # 手动标记死亡
        self.add_transition(StateTransition(
            from_state=AccountStatus.ACTIVE,
            to_state=AccountStatus.DEAD,
            allowed_roles=["data_clerk", "admin"],
            action=self._on_mark_as_dead_manual,
            description="手动标记账户为死亡"
        ))

        # 归档账户
        self.add_transition(StateTransition(
            from_state=AccountStatus.DEAD,
            to_state=AccountStatus.ARCHIVED,
            allowed_roles=["admin"],
            condition=lambda ctx: self._can_archive(ctx),
            action=self._on_archive,
            description="归档账户"
        ))

        # 暂停账户死亡
        self.add_transition(StateTransition(
            from_state=AccountStatus.SUSPENDED,
            to_state=AccountStatus.DEAD,
            allowed_roles=["system", "data_clerk", "admin"],
            auto=True,
            condition=lambda ctx: self._should_suspended_become_dead(ctx),
            action=self._on_suspended_become_dead,
            description="暂停账户转为死亡"
        ))

    def _should_enter_testing(self, context: Dict) -> bool:
        """判断是否应该进入测试期"""
        created_date = context.get("created_date")
        if created_date:
            days_since_creation = (datetime.utcnow() - created_date).days
            return days_since_creation >= 7
        return False

    def _should_become_active(self, context: Dict) -> bool:
        """判断是否应该转为正常投放"""
        # 测试期7天以上且日均消耗>100USD
        test_days = context.get("testing_days", 0)
        avg_spend = context.get("avg_daily_spend", 0)

        return test_days >= 7 and avg_spend > 100

    def _should_mark_as_dead(self, context: Dict) -> bool:
        """判断是否应该标记为死亡"""
        # 根据API反馈或长时间无消耗判断
        last_activity = context.get("last_activity")
        if last_activity:
            days_inactive = (datetime.utcnow() - last_activity).days
            return days_inactive >= 30  # 30天无活动

        # 根据API状态判断
        api_status = context.get("api_status")
        return api_status == "disabled"

    def _should_suspended_become_dead(self, context: Dict) -> bool:
        """判断暂停账户是否应该转为死亡"""
        suspended_date = context.get("suspended_date")
        if suspended_date:
            days_suspended = (datetime.utcnow() - suspended_date).days
            return days_suspended >= 14  # 暂停14天转为死亡
        return False

    def _can_suspend(self, context: Dict) -> bool:
        """判断是否可以暂停"""
        # 检查是否有待处理的充值申请
        pending_topups = context.get("pending_topups", 0)
        if pending_topups > 0:
            raise ValueError("有待处理的充值申请，无法暂停")

        return True

    def _can_resume(self, context: Dict) -> bool:
        """判断是否可以激活"""
        # 检查暂停原因是否已解决
        suspension_reason = context.get("suspension_reason", "")
        if "余额不足" in suspension_reason:
            current_balance = context.get("current_balance", 0)
            if current_balance < 100:
                return False

        return True

    def _can_archive(self, context: Dict) -> bool:
        """判断是否可以归档"""
        # 确保没有未处理的业务
        pending_reports = context.get("pending_reports", 0)
        pending_topups = context.get("pending_topups", 0)

        return pending_reports == 0 and pending_topups == 0

    async def _on_enter_testing(self, context: Dict) -> Dict:
        """进入测试期"""
        # 记录状态变更
        await self._log_status_change(
            context["account_id"],
            AccountStatus.NEW,
            AccountStatus.TESTING,
            "自动进入7天测试期",
            context["user_id"]
        )

        # 发送通知
        await notification_service.send_account_testing_notification(context["account_id"])

        return {"entered_testing": True}

    async def _on_enter_testing_manual(self, context: Dict) -> Dict:
        """手动进入测试期"""
        await self._log_status_change(
            context["account_id"],
            AccountStatus.NEW,
            AccountStatus.TESTING,
            f"手动激活测试期: {context.get('reason', '')}",
            context["user_id"]
        )

        return {"entered_testing": True}

    async def _on_become_active(self, context: Dict) -> Dict:
        """转为正常投放"""
        await self._log_status_change(
            context["account_id"],
            AccountStatus.TESTING,
            AccountStatus.ACTIVE,
            f"满足激活条件: 测试期{context.get('testing_days')}天, 日均消耗${context.get('avg_daily_spend')}",
            context["user_id"] if "user_id" in context else "system"
        )

        # 激活广告系列
        await self._activate_ad_campaigns(context["account_id"])

        return {"became_active": True}

    async def _on_activate_manual(self, context: Dict) -> Dict:
        """手动激活"""
        await self._log_status_change(
            context["account_id"],
            AccountStatus.TESTING,
            AccountStatus.ACTIVE,
            f"手动激活: {context.get('reason', '')}",
            context["user_id"]
        )

        await self._activate_ad_campaigns(context["account_id"])

        return {"activated": True}

    async def _on_suspend(self, context: Dict) -> Dict:
        """暂停账户"""
        await self._log_status_change(
            context["account_id"],
            AccountStatus.ACTIVE,
            AccountStatus.SUSPENDED,
            f"暂停投放: {context.get('reason', '')}",
            context["user_id"]
        )

        # 暂停广告系列
        await self._pause_ad_campaigns(context["account_id"])

        return {"suspended": True}

    async def _on_resume(self, context: Dict) -> Dict:
        """激活暂停的账户"""
        await self._log_status_change(
            context["account_id"],
            AccountStatus.SUSPENDED,
            AccountStatus.ACTIVE,
            f"恢复投放: 暂停原因已解决",
            context["user_id"]
        )

        # 恢复广告系列
        await self._resume_ad_campaigns(context["account_id"])

        return {"resumed": True}

    async def _on_mark_as_dead(self, context: Dict) -> Dict:
        """标记为死亡"""
        await self._log_status_change(
            context["account_id"],
            AccountStatus.ACTIVE,
            AccountStatus.DEAD,
            "账户死亡",
            context["user_id"] if "user_id" in context else "system"
        )

        # 停用所有广告系列
        await self._disable_all_campaigns(context["account_id"])

        # 发送死亡通知
        await notification_service.send_account_death_notification(context["account_id"])

        return {"marked_as_dead": True}

    async def _on_mark_as_dead_manual(self, context: Dict) -> Dict:
        """手动标记为死亡"""
        await self._log_status_change(
            context["account_id"],
            AccountStatus.ACTIVE,
            AccountStatus.DEAD,
            f"手动标记为死亡: {context.get('reason', '')}",
            context["user_id"]
        )

        await self._disable_all_campaigns(context["account_id"])

        return {"marked_as_dead": True}

    async def _on_suspended_become_dead(self, context: Dict) -> Dict:
        """暂停账户转为死亡"""
        await self._log_status_change(
            context["account_id"],
            AccountStatus.SUSPENDED,
            AccountStatus.DEAD,
            "暂停账户转为死亡",
            "system"
        )

        await self._disable_all_campaigns(context["account_id"])

        return {"suspended_to_dead": True}

    async def _on_archive(self, context: Dict) -> Dict:
        """归档账户"""
        await self._log_status_change(
            context["account_id"],
            AccountStatus.DEAD,
            AccountStatus.ARCHIVED,
            "账户归档",
            context["user_id"]
        )

        # 清理相关数据
        await self._cleanup_account_data(context["account_id"])

        return {"archived": True}

    # 私有辅助方法
    async def _log_status_change(self, account_id: str, old_status: AccountStatus, new_status: AccountStatus, reason: str, user_id: str):
        """记录状态变更"""
        # 实现状态变更记录逻辑
        pass

    async def _activate_ad_campaigns(self, account_id: str):
        """激活广告系列"""
        # 实现广告系列激活逻辑
        pass

    async def _pause_ad_campaigns(self, account_id: str):
        """暂停广告系列"""
        # 实现广告系列暂停逻辑
        pass

    async def _resume_ad_campaigns(self, account_id: str):
        """恢复广告系列"""
        # 实现广告系列恢复逻辑
        pass

    async def _disable_all_campaigns(self, account_id: str):
        """停用所有广告系列"""
        # 实现广告系列停用逻辑
        pass

    async def _cleanup_account_data(self, account_id: str):
        """清理账户相关数据"""
        # 实现数据清理逻辑
        pass
```

---

## 5. 状态机服务集成

### 5.1 统一状态机服务
```python
# services/state_machine_service.py
from typing import Dict, Optional, Any
from backend.services.topup_state_machine import TopupStateMachine
from backend.services.daily_report_state_machine import DailyReportStateMachine
from backend.services.account_state_machine import AccountStateMachine

class StateMachineService:
    """状态机服务统一入口"""

    def __init__(self):
        self.machines = {
            "topup": TopupStateMachine,
            "daily_report": DailyReportStateMachine,
            "account": AccountStateMachine
        }

    async def transition(
        self,
        entity_type: str,
        entity_id: str,
        to_state: str,
        user_id: str,
        user_role: str,
        reason: str = None,
        context: Dict = None
    ) -> Dict:
        """执行状态转换"""
        if entity_type not in self.machines:
            raise ValueError(f"不支持的实体类型: {entity_type}")

        machine_class = self.machines[entity_type]

        # 转换状态字符串为枚举
        to_state_enum = self._string_to_state(machine_class, to_state)

        # 获取当前状态
        current_state = await self._get_current_state(entity_type, entity_id)
        if current_state:
            machine = machine_class(current_state)
        else:
            machine = machine_class()

        # 准备上下文
        context = context or {}
        context.update({
            "entity_id": entity_id,
            "user_id": user_id,
            "user_role": user_role
        })

        # 执行状态转换
        try:
            result = await machine.transition(
                to_state=to_state_enum,
                user_id=user_id,
                user_role=user_role,
                reason=reason,
                context=context
            )
            return result
        except Exception as e:
            logger.error(f"状态转换失败: {e}")
            raise

    def _string_to_state(self, machine_class, state_str: str):
        """将状态字符串转换为枚举"""
        state_map = {
            TopupStateMachine: TopupStatus,
            DailyReportStateMachine: DailyReportStatus,
            AccountStateMachine: AccountStatus
        }

        state_enum = state_map.get(machine_class)
        if not state_enum:
            raise ValueError(f"无效的状态字符串: {state_str}")

        for state in state_enum:
            if state.value == state_str:
                return state

        raise ValueError(f"状态'{state_str}'在{machine_class.__name__}中不存在")

    async def _get_current_state(self, entity_type: str, entity_id: str) -> Optional[Any]:
        """获取实体当前状态"""
        # 从数据库获取当前状态
        # 这里需要根据entity_type查询不同的表
        pass

    def get_available_transitions(self, entity_type: str, entity_id: str, user_role: str) -> List[str]:
        """获取可用的状态转换"""
        if entity_type not in self.machines:
            return []

        # 获取当前状态并创建状态机实例
        current_state = await self._get_current_state(entity_type, entity_id)
        if not current_state:
            return []

        machine_class = self.machines[entity_type]
        machine = machine_class(current_state)

        # 获取可用转换
        available_states = machine.get_available_transitions(user_role)
        return [state.value for state in available_states]

    def get_transition_history(
        self,
        entity_type: str,
        entity_id: str,
        limit: int = None
    ) -> List[Dict]:
        """获取转换历史"""
        # 从数据库查询转换历史
        # 这里需要根据entity_id查询状态变更历史表
        pass

    def validate_transition(
        self,
        entity_type: str,
        current_state: str,
        target_state: str,
        user_role: str,
        context: Dict = None
    ) -> bool:
        """验证状态转换是否有效"""
        if entity_type not in self.machines:
            return False

        machine_class = self.machines[entity_type]

        try:
            current_state_enum = self._string_to_state(machine_class, current_state)
            target_state_enum = self._string_to_state(machine_class, target_state)

            # 创建临时状态机实例进行验证
            machine = machine_class(current_state_enum)
            return machine.can_transition(target_state_enum, user_role, context)
        except ValueError:
            return False
```

### 5.2 状态机API端点
```python
# routers/state_machine.py
from fastapi import APIRouter, Depends, HTTPException
from backend.services.state_machine_service import StateMachineService
from backend.dependencies.auth import get_current_user
from backend.schemas.state_machine import StateTransitionRequest

router = APIRouter(prefix="/api/state-machine", tags=["state_machine"])

@router.post("/{entity_type}/{entity_id}/transition")
async def transition_state(
    entity_type: str,
    entity_id: str,
    request: StateTransitionRequest,
    current_user: dict = Depends(get_current_user)
):
    """执行状态转换"""
    try:
        # 权限检查
        if not _can_transition_entity(current_user["role"], entity_type):
            raise HTTPException(status_code=403, detail="无权限操作该实体类型")

        # 执行状态转换
        state_service = StateMachineService()
        result = await state_service.transition(
            entity_type=entity_type,
            entity_id=entity_id,
            to_state=request.to_state,
            user_id=current_user["user_id"],
            user_role=current_user["role"],
            reason=request.reason,
            context=request.context or {}
        )

        return {
            "success": True,
            "data": result,
            "message": "状态转换成功"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"状态转换失败: {e}")
        raise HTTPException(status_code=500, detail="服务器内部错误")

@router.get("/{entity_type}/{entity_id}/available-transitions")
async def get_available_transitions(
    entity_type: str,
    entity_id: str,
    current_user: dict = Depends(get_current_user)
):
    """获取可用的状态转换"""
    try:
        if not _can_view_entity(current_user["role"], entity_type):
            raise HTTPException(status_code=403, detail="无权限查看该实体类型")

        state_service = StateMachineService()
        available_states = state_service.get_available_transitions(
            entity_type=entity_type,
            entity_id=entity_id,
            user_role=current_user["role"]
        )

        return {
            "success": True,
            "data": {
                "available_states": available_states,
                "entity_type": entity_type,
                "entity_id": entity_id
            }
        }

    except Exception as e:
        logger.error(f"获取可用状态转换失败: {e}")
        raise HTTPException(status_code=500, detail="服务器内部错误")

@router.get("/{entity_type}/{entity_id}/history")
async def get_transition_history(
    entity_type: str,
    entity_id: str,
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """获取状态转换历史"""
    try:
        if not _can_view_entity(current_user["role"], entity_type):
            raise HTTPException(status_code=403, detail="无权限查看该实体类型")

        state_service = StateMachineService()
        history = state_service.get_transition_history(
            entity_type=entity_type,
            entity_id=entity_id,
            limit=limit
        )

        return {
            "success": True,
            "data": {
                "history": history,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "total_count": len(history)
            }
        }

    except Exception as e:
        logger.error(f"获取状态历史失败: {e}")
        raise HTTPException(status_code=500, detail="服务器内部错误")

def _can_transition_entity(user_role: str, entity_type: str) -> bool:
    """检查用户是否可以转换实体类型"""
    # 管理员可以转换所有实体
    if user_role == "admin":
        return True

    # 不同角色的权限
    role_permissions = {
        "media_buyer": ["daily_report", "topup"],
        "data_clerk": ["daily_report", "topup", "account"],
        "finance": ["topup"],
        "manager": ["project", "account"]
    }

    return entity_type in role_permissions.get(user_role, [])

def _can_view_entity(user_role: str, entity_type: str) -> bool:
    """检查用户是否可以查看实体类型"""
    # 所有角色都可以查看状态机信息
    return True
```

---

## 6. 状态机表数据

### 6.1 状态转换记录表
```sql
CREATE TABLE state_transition_history (
    -- 主键
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 实体信息
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,

    -- 状态信息
    from_state VARCHAR(50) NOT NULL,
    to_state VARCHAR(50) NOT NULL,

    -- 用户信息
    user_id UUID NOT NULL REFERENCES users(id),
    user_role VARCHAR(50) NOT NULL,

    -- 转换信息
    reason TEXT,
    context JSONB,

    -- 系统信息
    auto_transition BOOLEAN DEFAULT false,
    action_type VARCHAR(50),

    -- 时间信息
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_state_history_entity ON state_transition_history(entity_type, entity_id);
CREATE INDEX idx_state_history_user ON state_transition_history(user_id);
CREATE INDEX idx_state_history_created_at ON state_transition_history(created_at);
```

### 6.2 状态机配置表
```sql
CREATE TABLE state_machine_configs (
    -- 主键
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 配置信息
    entity_type VARCHAR(50) NOT NULL UNIQUE,
    config_name VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT true,

    -- 配置数据
    config_data JSONB NOT NULL,

    -- 审计信息
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 示例配置
INSERT INTO state_machine_configs (entity_type, config_name, config_data) VALUES
('topup', 'default_config', '{
    "auto_transitions": {
        "testing_to_active": {
            "min_testing_days": 7,
            "min_daily_spend": 100
        },
        "auto_suspension_check": {
            "inactive_days_threshold": 3
        },
        "auto_death_detection": {
            "inactive_days_threshold": 30
        }
    }
}');
```

---

## 7. 监控和告警

### 7.1 状态变更监控
```python
# services/state_machine_monitor.py
import logging
from typing import List, Dict
from datetime import datetime, timedelta
from backend.services.state_machine_service import StateMachineService

logger = logging.getLogger(__name__)

class StateMachineMonitor:
    """状态机监控"""

    def __init__(self):
        self.state_service = StateMachineService()

    async def check_stuck_transitions(self, hours: int = 24) -> List[Dict]:
        """检查卡住的状态转换"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        # 查询长时间未处理的转换
        stuck_transitions = []

        for entity_type in ["topup", "daily_report", "account"]:
            try:
                history = await self.state_service.get_transition_history(
                    entity_type,
                    None,  # 获取所有记录
                    limit=100
                )

                # 检查长时间未更新的状态
                for entry in history:
                    entry_time = datetime.fromisoformat(entry["timestamp"])
                    if entry_time > cutoff_time:
                        # 检查实体当前状态
                        current_state = await self.state_service._get_current_state(
                            entity_type,
                            entry["entity_id"]
                        )

                        # 如果状态转换后长时间没有进一步转换
                        if current_state == entry["to_state"]:
                            stuck_transitions.append({
                                "entity_type": entity_type,
                                "entity_id": entry["entity_id"],
                                "stuck_state": current_state.value if current_state else None,
                                "stuck_hours": (datetime.utcnow() - entry_time).total_seconds() / 3600,
                                "last_transition": entry["timestamp"]
                            })

            except Exception as e:
                logger.error(f"检查{entity_type}状态转换失败: {e}")

        return stuck_transitions

    async def check_anomalous_transitions(self) -> List[Dict]:
        """检查异常状态转换"""
        anomalies = []

        # 检查异常的转换模式
        anomaly_patterns = [
            {
                "name": "频繁拒绝",
                "condition": lambda history: self._detect_frequent_rejections(history),
                "severity": "medium"
            },
            {
                "name": "循环转换",
                "condition": lambda history: self._detect_circular_transitions(history),
                "severity": "high"
            },
            {
                "name": "超时转换",
                "condition": lambda history: self._detect_timeout_transitions(history),
                "severity": "medium"
            }
        ]

        for entity_type in ["topup", "daily_report", "account"]:
            try:
                history = await self.state_service.get_transition_history(
                    entity_type,
                    None,
                    limit=100
                )

                for pattern in anomaly_patterns:
                    if pattern["condition"](history):
                        anomalies.append({
                            "entity_type": entity_type,
                            "anomaly_type": pattern["name"],
                            "severity": pattern["severity"],
                            "details": pattern["condition"](history)
                        })

            except Exception as e:
                logger.error(f"检查{entity_type}异常模式失败: {e}")

        return anomalies

    def _detect_frequent_rejections(self, history: List[Dict]) -> bool:
        """检测频繁拒绝"""
        rejected_count = len([h for h in history if "rejected" in h.get("to_state", "")])
        total_count = len(history)
        return total_count > 0 and (rejected_count / total_count) > 0.3

    def _detect_circular_transitions(self, history: List[Dict]) -> bool:
        """检测循环转换"""
        # 简单的循环检测：A->B->A 模式
        for i in range(len(history) - 1):
            current = history[i]
            next_entry = history[i + 1]

            if (current["from_state"] == next_entry["to_state"] and
                next_entry["from_state"] == current["to_state"]):
                return True

        return False

    def _detect_timeout_transitions(self, history: List[Dict]) -> bool:
        """检测超时转换"""
        for entry in history:
            if not entry.get("auto_transition"):
                # 非自动转换检查是否超时
                entry_time = datetime.fromisoformat(entry["timestamp"])
                if datetime.utcnow() - entry_time > timedelta(hours=48):
                    return True
        return False

    async def generate_state_metrics(self) -> Dict:
        """生成状态机指标"""
        metrics = {}

        for entity_type in ["topup", "daily_report", "account"]:
            try:
                history = await self.state_service.get_transition_history(
                    entity_type,
                    None,
                    limit=1000
                )

                if history:
                    total_transitions = len(history)
                    successful_transitions = len([h for h in history if "success" in str(h.get("details", {}))])

                    # 计算转换成功率
                    success_rate = (successful_transitions / total_transitions) * 100 if total_transitions > 0 else 0

                    # 统计各状态的数量
                    state_counts = {}
                    for entry in history:
                        state = entry["to_state"]
                        state_counts[state] = state_counts.get(state, 0) + 1

                    metrics[entity_type] = {
                        "total_transitions": total_transitions,
                        "success_rate": round(success_rate, 2),
                        "state_distribution": state_counts,
                        "last_transition": history[-1]["timestamp"] if history else None
                    }

            except Exception as e:
                logger.error(f"生成{entity_type}指标失败: {e}")
                metrics[entity_type] = {"error": str(e)}

        return metrics
```

---

**文档版本**: v2.0
**最后更新**: 2025-11-10
**负责人**: 业务流程架构师
**审核人**: 产品负责人