"""
结构化 SoT 加载器

使用 YAML 配置文件替代正则解析，提供更可靠的 SoT 数据访问。

版本: v7.0
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, FrozenSet
from dataclasses import dataclass, field
import yaml

logger = logging.getLogger(__name__)

# 配置目录
CONFIG_DIR = Path(__file__).parent / "config"


@dataclass
class RoleDefinition:
    """角色定义"""
    id: str
    name: str
    permissions: List[str]
    description: str = ""


@dataclass
class StateDefinition:
    """状态定义"""
    id: str
    name: str
    description: str = ""
    is_initial: bool = False
    is_terminal: bool = False
    next_states: List[str] = field(default_factory=list)


@dataclass
class ErrorCodeDefinition:
    """错误码定义"""
    code: str
    message: str
    description: str = ""


@dataclass
class SotConfig:
    """SoT 配置数据"""
    
    # 角色
    technical_roles: Dict[str, RoleDefinition] = field(default_factory=dict)
    business_to_technical: Dict[str, Optional[str]] = field(default_factory=dict)
    deprecated_roles: FrozenSet[str] = field(default_factory=frozenset)
    
    # 状态
    daily_report_states: Dict[str, StateDefinition] = field(default_factory=dict)
    deprecated_daily_report_states: FrozenSet[str] = field(default_factory=frozenset)
    topup_states: Dict[str, StateDefinition] = field(default_factory=dict)
    
    # 错误码
    error_codes: Dict[str, ErrorCodeDefinition] = field(default_factory=dict)
    
    def get_allowed_roles(self) -> FrozenSet[str]:
        """获取允许的角色集合"""
        return frozenset(self.technical_roles.keys())
    
    def get_allowed_daily_report_states(self) -> FrozenSet[str]:
        """获取允许的日报状态集合"""
        return frozenset(self.daily_report_states.keys())
    
    def get_allowed_topup_states(self) -> FrozenSet[str]:
        """获取允许的充值状态集合"""
        return frozenset(self.topup_states.keys())
    
    def is_valid_role(self, role: str) -> bool:
        """检查角色是否有效"""
        return role in self.technical_roles
    
    def is_deprecated_role(self, role: str) -> bool:
        """检查角色是否已废弃"""
        return role in self.deprecated_roles
    
    def is_valid_daily_report_state(self, state: str) -> bool:
        """检查日报状态是否有效"""
        return state in self.daily_report_states
    
    def is_valid_state_transition(
        self,
        state_machine: str,
        from_state: str,
        to_state: str,
    ) -> bool:
        """检查状态转换是否有效"""
        if state_machine == "daily_report":
            states = self.daily_report_states
        elif state_machine == "topup":
            states = self.topup_states
        else:
            return False
        
        if from_state not in states:
            return False
        
        return to_state in states[from_state].next_states
    
    def is_valid_error_code(self, code: str) -> bool:
        """检查错误码是否有效"""
        return code in self.error_codes


class StructuredSotLoader:
    """
    结构化 SoT 加载器
    
    从 YAML 配置文件加载 SoT 数据，替代正则解析。
    
    优势:
    1. 配置即文档: YAML 文件清晰可读
    2. 类型安全: 使用 dataclass 提供类型检查
    3. 可维护: 修改配置无需改代码
    4. 可验证: 加载时验证配置完整性
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        初始化加载器
        
        Args:
            config_dir: 配置目录，默认为 sot/config/
        """
        self.config_dir = config_dir or CONFIG_DIR
        self._config: Optional[SotConfig] = None
    
    def load(self) -> SotConfig:
        """
        加载 SoT 配置
        
        Returns:
            SotConfig 数据对象
        """
        if self._config is not None:
            return self._config
        
        config = SotConfig()
        
        # 加载角色配置
        roles_file = self.config_dir / "roles.yaml"
        if roles_file.exists():
            self._load_roles(config, roles_file)
        
        # 加载状态配置
        states_file = self.config_dir / "states.yaml"
        if states_file.exists():
            self._load_states(config, states_file)
        
        # 加载错误码配置
        error_codes_file = self.config_dir / "error_codes.yaml"
        if error_codes_file.exists():
            self._load_error_codes(config, error_codes_file)
        
        self._config = config
        logger.info(
            f"SoT 配置加载完成: "
            f"{len(config.technical_roles)} 角色, "
            f"{len(config.daily_report_states)} 日报状态, "
            f"{len(config.error_codes)} 错误码"
        )
        
        return config
    
    def _load_roles(self, config: SotConfig, file_path: Path) -> None:
        """加载角色配置"""
        try:
            with open(file_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            if data is None:
                return
            
            # 技术层角色
            for role_data in data.get("technical_roles", []):
                role = RoleDefinition(
                    id=role_data["id"],
                    name=role_data["name"],
                    permissions=role_data.get("permissions", []),
                    description=role_data.get("description", ""),
                )
                config.technical_roles[role.id] = role
            
            # 业务层到技术层映射
            config.business_to_technical = data.get("business_to_technical_mapping", {})
            
            # 废弃角色
            config.deprecated_roles = frozenset(data.get("deprecated_roles", []))
            
        except Exception as e:
            logger.error(f"加载角色配置失败: {e}")
    
    def _load_states(self, config: SotConfig, file_path: Path) -> None:
        """加载状态配置"""
        try:
            with open(file_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            if data is None:
                return
            
            # 日报状态
            for state_data in data.get("daily_report_states", []):
                state = StateDefinition(
                    id=state_data["id"],
                    name=state_data["name"],
                    description=state_data.get("description", ""),
                    is_initial=state_data.get("is_initial", False),
                    is_terminal=state_data.get("is_terminal", False),
                    next_states=state_data.get("next_states", []),
                )
                config.daily_report_states[state.id] = state
            
            # 废弃日报状态
            config.deprecated_daily_report_states = frozenset(
                data.get("deprecated_daily_report_states", [])
            )
            
            # 充值状态
            for state_data in data.get("topup_states", []):
                state = StateDefinition(
                    id=state_data["id"],
                    name=state_data["name"],
                    description=state_data.get("description", ""),
                    is_initial=state_data.get("is_initial", False),
                    is_terminal=state_data.get("is_terminal", False),
                    next_states=state_data.get("next_states", []),
                )
                config.topup_states[state.id] = state
            
        except Exception as e:
            logger.error(f"加载状态配置失败: {e}")
    
    def _load_error_codes(self, config: SotConfig, file_path: Path) -> None:
        """加载错误码配置"""
        try:
            with open(file_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            if data is None:
                return
            
            # 已注册错误码
            for code_data in data.get("registered_codes", []):
                error_code = ErrorCodeDefinition(
                    code=code_data["code"],
                    message=code_data["message"],
                    description=code_data.get("description", ""),
                )
                config.error_codes[error_code.code] = error_code
            
        except Exception as e:
            logger.error(f"加载错误码配置失败: {e}")
    
    def validate(self) -> List[str]:
        """
        验证 SoT 配置完整性
        
        Returns:
            错误消息列表 (空列表表示验证通过)
        """
        errors = []
        config = self.load()
        
        # 验证角色
        if not config.technical_roles:
            errors.append("缺少技术层角色定义")
        
        # 验证日报状态
        if not config.daily_report_states:
            errors.append("缺少日报状态定义")
        else:
            # 检查是否有初始状态
            has_initial = any(s.is_initial for s in config.daily_report_states.values())
            if not has_initial:
                errors.append("日报状态缺少初始状态")
            
            # 检查是否有终态
            has_terminal = any(s.is_terminal for s in config.daily_report_states.values())
            if not has_terminal:
                errors.append("日报状态缺少终态")
            
            # 检查状态转换引用是否有效
            for state in config.daily_report_states.values():
                for next_state in state.next_states:
                    if next_state not in config.daily_report_states:
                        errors.append(
                            f"状态 {state.id} 引用了无效的下一状态: {next_state}"
                        )
        
        return errors


# =============================================================================
# 便捷函数
# =============================================================================

_loader: Optional[StructuredSotLoader] = None


def get_sot_config() -> SotConfig:
    """获取 SoT 配置 (单例)"""
    global _loader
    if _loader is None:
        _loader = StructuredSotLoader()
    return _loader.load()


def validate_sot_config() -> List[str]:
    """验证 SoT 配置"""
    global _loader
    if _loader is None:
        _loader = StructuredSotLoader()
    return _loader.validate()


def is_valid_role(role: str) -> bool:
    """检查角色是否有效"""
    return get_sot_config().is_valid_role(role)


def is_valid_daily_report_state(state: str) -> bool:
    """检查日报状态是否有效"""
    return get_sot_config().is_valid_daily_report_state(state)


def is_valid_error_code(code: str) -> bool:
    """检查错误码是否有效"""
    return get_sot_config().is_valid_error_code(code)


__all__ = [
    "StructuredSotLoader",
    "SotConfig",
    "RoleDefinition",
    "StateDefinition",
    "ErrorCodeDefinition",
    "get_sot_config",
    "validate_sot_config",
    "is_valid_role",
    "is_valid_daily_report_state",
    "is_valid_error_code",
]
