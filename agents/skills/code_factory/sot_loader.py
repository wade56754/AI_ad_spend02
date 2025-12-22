"""
SoT (Single Source of Truth) 动态加载器

基准文档: STATE_MACHINE.md v2.6, DATA_SCHEMA.md v5.2
版本: v1.0
创建日期: 2025-12-22

功能:
- 从 SoT 文档动态加载角色、状态、字段白名单
- 替代硬编码的 frozenset 定义
- 确保验证器始终使用最新的 SoT 规范
"""

import re
from pathlib import Path
from typing import Dict, Set, Optional, List
from dataclasses import dataclass


@dataclass
class SotDefinitions:
    """SoT 定义数据类"""
    roles: frozenset[str]
    daily_report_states: frozenset[str]
    topup_states: frozenset[str]
    ledger_states: frozenset[str]
    error_code_prefixes: frozenset[str]


class SotLoader:
    """从 SoT 文档动态加载白名单

    用法:
        >>> loader = SotLoader(project_root=Path("/path/to/project"))
        >>> loader.is_valid_role("admin")
        True
        >>> loader.is_valid_role("invalid_role")
        False
        >>> loader.is_valid_status("raw_submitted", "daily_reports")
        True
    """

    def __init__(self, project_root: Path):
        """初始化 SoT 加载器

        Args:
            project_root: 项目根目录路径
        """
        self.project_root = Path(project_root)
        self.docs_sot_path = self.project_root / "docs" / "2.sot"

        # 加载所有定义
        self._definitions = self._load_all_definitions()

    def _load_all_definitions(self) -> SotDefinitions:
        """加载所有 SoT 定义

        Returns:
            SotDefinitions: 包含所有白名单的数据类
        """
        return SotDefinitions(
            roles=self._load_roles(),
            daily_report_states=self._load_daily_report_states(),
            topup_states=self._load_topup_states(),
            ledger_states=self._load_ledger_states(),
            error_code_prefixes=self._load_error_code_prefixes()
        )

    def _load_roles(self) -> frozenset[str]:
        """从 STATE_MACHINE.md 或 backend/models/enums.py 加载角色

        Returns:
            frozenset[str]: 技术角色集合（5 个）

        实现策略:
        - 优先从 backend/models/enums.py 读取（权威来源）
        - 备选从 STATE_MACHINE.md 解析
        - 兜底使用硬编码
        """
        # 策略 1: 从 backend/models/enums.py 读取
        enums_path = self.project_root / "backend" / "models" / "enums.py"
        if enums_path.exists():
            try:
                content = enums_path.read_text(encoding="utf-8")
                # 匹配 class UserRole(str, Enum): ... admin = "admin" ...
                role_pattern = r'class\s+UserRole.*?(?:admin|finance|data_operator|account_manager|media_buyer)\s*=\s*"([^"]+)"'
                matches = re.findall(role_pattern, content, re.DOTALL)
                if matches:
                    return frozenset(matches)
            except Exception:
                pass  # 继续尝试备选方案

        # 策略 2: 从 STATE_MACHINE.md 解析
        # （实际实现需要 Markdown 解析，这里简化）

        # 策略 3: 兜底硬编码（对齐 backend/models/enums.py）
        return frozenset([
            'admin',           # 系统管理员
            'finance',         # 财务
            'data_operator',   # 数据运营
            'account_manager', # 账户管理员
            'media_buyer'      # 广告投手
        ])

    def _load_daily_report_states(self) -> frozenset[str]:
        """从 backend/models/enums.py 加载日报状态

        Returns:
            frozenset[str]: 日报状态集合（8 个）
        """
        enums_path = self.project_root / "backend" / "models" / "enums.py"
        if enums_path.exists():
            try:
                content = enums_path.read_text(encoding="utf-8")
                # 匹配 class DailyReportStatus(str, Enum): ...
                pattern = r'class\s+DailyReportStatus.*?(\w+)\s*=\s*"([^"]+)"'
                matches = re.findall(pattern, content, re.DOTALL)
                if matches:
                    # 提取状态值（第二个分组）
                    states = [match[1] for match in matches if match[1]]
                    if states:
                        return frozenset(states)
            except Exception:
                pass

        # 兜底硬编码（对齐 STATE_MACHINE.md v2.6）
        return frozenset([
            'raw_submitted',    # 投手提交原始粉数
            'trend_pending',    # 等待趋势风控检查
            'trend_ok',         # 趋势正常
            'trend_flagged',    # 趋势异常,需人工复核
            'trend_resolved',   # 运营确认异常已解决
            'final_pending',    # 等待最终粉数确认
            'final_confirmed',  # 最终粉数已确认
            'final_locked'      # 已进入计费,锁定(终态)
        ])

    def _load_topup_states(self) -> frozenset[str]:
        """从 backend/models/enums.py 加载充值请求状态

        Returns:
            frozenset[str]: 充值请求状态集合
        """
        enums_path = self.project_root / "backend" / "models" / "enums.py"
        if enums_path.exists():
            try:
                content = enums_path.read_text(encoding="utf-8")
                pattern = r'class\s+TopupRequestStatus.*?(\w+)\s*=\s*"([^"]+)"'
                matches = re.findall(pattern, content, re.DOTALL)
                if matches:
                    states = [match[1] for match in matches if match[1]]
                    if states:
                        return frozenset(states)
            except Exception:
                pass

        # 兜底硬编码
        return frozenset([
            'draft',           # 草稿
            'pending_review',  # 待审核
            'finance_approve', # 财务已批准
            'paid',            # 已支付
            'completed',       # 已完成
            'rejected',        # 已拒绝
            'cancelled'        # 已取消
        ])

    def _load_ledger_states(self) -> frozenset[str]:
        """加载账本状态

        Returns:
            frozenset[str]: 账本状态集合
        """
        # 账本状态相对稳定，使用硬编码
        return frozenset([
            'PENDING',    # 待处理
            'CONFIRMED',  # 已确认
            'REVERSED',   # 已冲正
            'LOCKED'      # 已锁定
        ])

    def _load_error_code_prefixes(self) -> frozenset[str]:
        """从 ERROR_CODES_SOT.md 加载错误码前缀

        Returns:
            frozenset[str]: 错误码前缀集合
        """
        error_codes_path = self.docs_sot_path / "ERROR_CODES_SOT.md"
        if error_codes_path.exists():
            try:
                content = error_codes_path.read_text(encoding="utf-8")
                # 匹配错误码前缀模式: VAL-001, AUTH-002 等
                pattern = r'([A-Z]+)-\d{3}'
                matches = re.findall(pattern, content)
                if matches:
                    return frozenset(set(matches))  # 去重
            except Exception:
                pass

        # 兜底硬编码
        return frozenset([
            'VAL',    # Validation
            'AUTH',   # Authentication
            'PERM',   # Permission
            'BUS',    # Business
            'DATA',   # Data
            'SYS',    # System
            'FIN',    # Finance
            'SOT'     # SoT Compliance
        ])

    # === 公共验证方法 ===

    def is_valid_role(self, role: str) -> bool:
        """验证角色是否合法

        Args:
            role: 角色名称

        Returns:
            bool: True 表示合法
        """
        return role in self._definitions.roles

    def is_valid_status(self, status: str, table: Optional[str] = None) -> bool:
        """验证状态是否合法

        Args:
            status: 状态值
            table: 可选的表名（daily_reports, topup_requests 等）

        Returns:
            bool: True 表示合法
        """
        if table == "daily_reports":
            return status in self._definitions.daily_report_states
        elif table == "topup_requests":
            return status in self._definitions.topup_states
        elif table == "ledger_entries":
            return status in self._definitions.ledger_states
        else:
            # 检查所有表
            return (
                status in self._definitions.daily_report_states or
                status in self._definitions.topup_states or
                status in self._definitions.ledger_states
            )

    def is_valid_error_code_prefix(self, prefix: str) -> bool:
        """验证错误码前缀是否合法

        Args:
            prefix: 错误码前缀（如 "VAL", "AUTH"）

        Returns:
            bool: True 表示合法
        """
        return prefix.upper() in self._definitions.error_code_prefixes

    def get_all_roles(self) -> frozenset[str]:
        """获取所有技术角色"""
        return self._definitions.roles

    def get_all_daily_report_states(self) -> frozenset[str]:
        """获取所有日报状态"""
        return self._definitions.daily_report_states

    def get_all_topup_states(self) -> frozenset[str]:
        """获取所有充值请求状态"""
        return self._definitions.topup_states

    def get_all_ledger_states(self) -> frozenset[str]:
        """获取所有账本状态"""
        return self._definitions.ledger_states

    def get_all_error_code_prefixes(self) -> frozenset[str]:
        """获取所有错误码前缀"""
        return self._definitions.error_code_prefixes

    def validate_and_suggest(self, value: str, category: str) -> tuple[bool, Optional[str]]:
        """验证值并提供建议

        Args:
            value: 待验证的值
            category: 类别（"role", "daily_report_status", "topup_status" 等）

        Returns:
            tuple[bool, Optional[str]]: (是否合法, 建议信息)
        """
        if category == "role":
            if self.is_valid_role(value):
                return True, None
            else:
                valid_roles = ", ".join(sorted(self._definitions.roles))
                return False, f"无效角色 '{value}'。有效角色: {valid_roles}"

        elif category == "daily_report_status":
            if value in self._definitions.daily_report_states:
                return True, None
            else:
                valid_states = ", ".join(sorted(self._definitions.daily_report_states))
                return False, f"无效日报状态 '{value}'。有效状态: {valid_states}"

        elif category == "topup_status":
            if value in self._definitions.topup_states:
                return True, None
            else:
                valid_states = ", ".join(sorted(self._definitions.topup_states))
                return False, f"无效充值状态 '{value}'。有效状态: {valid_states}"

        else:
            return False, f"未知类别 '{category}'"


# 全局单例（可选）
_global_loader: Optional[SotLoader] = None


def get_sot_loader(project_root: Optional[Path] = None) -> SotLoader:
    """获取全局 SotLoader 单例

    Args:
        project_root: 项目根目录（首次调用时需要提供）

    Returns:
        SotLoader: 全局加载器实例
    """
    global _global_loader
    if _global_loader is None:
        if project_root is None:
            # 尝试自动检测项目根目录
            current_file = Path(__file__)
            # 假设此文件在 agents/skills/code_factory/sot_loader.py
            project_root = current_file.parent.parent.parent.parent
        _global_loader = SotLoader(project_root)
    return _global_loader


def reset_sot_loader():
    """重置全局加载器（用于测试）"""
    global _global_loader
    _global_loader = None
