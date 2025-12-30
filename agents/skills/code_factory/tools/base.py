"""
工具基类和注册表 v5.0

提供工具的基础架构:
- Tool 基类
- ToolResult 结果类
- ToolRegistry 注册表
- @tool 装饰器

基准文档: MASTER.md v4.6
版本: v5.0
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Type, Union
from enum import Enum
from functools import wraps
import time
import traceback


class ToolStatus(str, Enum):
    """工具执行状态"""
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    BLOCKED = "blocked"


@dataclass
class ToolResult:
    """工具执行结果"""
    status: ToolStatus
    output: Any = None
    error: Optional[str] = None
    duration_ms: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def success(self) -> bool:
        return self.status == ToolStatus.SUCCESS
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "output": self.output,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "metadata": self.metadata,
        }
    
    @classmethod
    def ok(cls, output: Any = None, **metadata) -> "ToolResult":
        """创建成功结果"""
        return cls(
            status=ToolStatus.SUCCESS,
            output=output,
            metadata=metadata,
        )
    
    @classmethod
    def fail(cls, error: str, **metadata) -> "ToolResult":
        """创建失败结果"""
        return cls(
            status=ToolStatus.ERROR,
            error=error,
            metadata=metadata,
        )
    
    @classmethod
    def blocked(cls, reason: str, **metadata) -> "ToolResult":
        """创建阻止结果"""
        return cls(
            status=ToolStatus.BLOCKED,
            error=reason,
            metadata=metadata,
        )


class Tool(ABC):
    """
    工具基类
    
    所有工具必须继承此类并实现:
    - name: 工具名称
    - description: 工具描述
    - execute(): 执行逻辑
    
    使用方式:
    ```python
    class MyTool(Tool):
        name = "my_tool"
        description = "我的工具"
        
        def execute(self, **kwargs) -> ToolResult:
            return ToolResult.ok(output="Hello")
    ```
    """
    
    # 子类必须定义
    name: str = ""
    description: str = ""
    
    # 可选配置
    timeout: int = 60  # 超时时间 (秒)
    requires_confirmation: bool = False  # 是否需要确认
    is_dangerous: bool = False  # 是否危险操作
    
    def __init__(self, **config):
        """初始化工具
        
        Args:
            **config: 工具配置
        """
        self.config = config
    
    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """执行工具
        
        Args:
            **kwargs: 工具参数
            
        Returns:
            ToolResult
        """
        pass
    
    def run(self, **kwargs) -> ToolResult:
        """运行工具 (带计时和异常处理)
        
        Args:
            **kwargs: 工具参数
            
        Returns:
            ToolResult
        """
        start_time = time.time()
        
        try:
            result = self.execute(**kwargs)
            result.duration_ms = int((time.time() - start_time) * 1000)
            return result
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return ToolResult(
                status=ToolStatus.ERROR,
                error=str(e),
                duration_ms=duration_ms,
                metadata={"traceback": traceback.format_exc()},
            )
    
    def get_schema(self) -> Dict[str, Any]:
        """获取工具 Schema (用于 LLM)
        
        Returns:
            Schema 字典
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.get_parameters(),
            "requires_confirmation": self.requires_confirmation,
            "is_dangerous": self.is_dangerous,
        }
    
    def get_parameters(self) -> Dict[str, Any]:
        """获取参数定义
        
        子类可覆盖此方法提供参数 Schema
        
        Returns:
            参数 Schema
        """
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }
    
    def validate(self, **kwargs) -> Optional[str]:
        """验证参数
        
        Args:
            **kwargs: 工具参数
            
        Returns:
            错误消息或 None
        """
        return None
    
    def __repr__(self) -> str:
        return f"<Tool {self.name}>"


class ToolRegistry:
    """
    工具注册表
    
    管理所有可用工具，提供:
    - 工具注册
    - 工具查找
    - 批量执行
    
    使用方式:
    ```python
    registry = ToolRegistry()
    
    # 注册工具
    registry.register(MyTool())
    
    # 获取工具
    tool = registry.get("my_tool")
    result = tool.run(param1="value")
    
    # 列出所有工具
    tools = registry.list_tools()
    ```
    """
    
    def __init__(self):
        """初始化注册表"""
        self._tools: Dict[str, Tool] = {}
    
    def register(self, tool: Tool) -> None:
        """注册工具
        
        Args:
            tool: 工具实例
        """
        if not tool.name:
            raise ValueError(f"工具必须有名称: {tool}")
        
        self._tools[tool.name] = tool
    
    def register_class(self, tool_class: Type[Tool], **config) -> None:
        """注册工具类
        
        Args:
            tool_class: 工具类
            **config: 工具配置
        """
        tool = tool_class(**config)
        self.register(tool)
    
    def unregister(self, name: str) -> bool:
        """注销工具
        
        Args:
            name: 工具名称
            
        Returns:
            是否成功
        """
        if name in self._tools:
            del self._tools[name]
            return True
        return False
    
    def get(self, name: str) -> Optional[Tool]:
        """获取工具
        
        Args:
            name: 工具名称
            
        Returns:
            Tool 或 None
        """
        return self._tools.get(name)
    
    def has(self, name: str) -> bool:
        """检查工具是否存在"""
        return name in self._tools
    
    def list_tools(self) -> List[str]:
        """列出所有工具名称"""
        return list(self._tools.keys())
    
    def get_all(self) -> List[Tool]:
        """获取所有工具"""
        return list(self._tools.values())
    
    def get_schemas(self) -> List[Dict[str, Any]]:
        """获取所有工具的 Schema"""
        return [tool.get_schema() for tool in self._tools.values()]
    
    def execute(self, name: str, **kwargs) -> ToolResult:
        """执行工具
        
        Args:
            name: 工具名称
            **kwargs: 工具参数
            
        Returns:
            ToolResult
        """
        tool = self.get(name)
        if tool is None:
            return ToolResult.fail(f"工具不存在: {name}")
        
        return tool.run(**kwargs)
    
    def __len__(self) -> int:
        return len(self._tools)
    
    def __contains__(self, name: str) -> bool:
        return name in self._tools


# ============================================================
# 装饰器
# ============================================================

def tool(
    name: str,
    description: str = "",
    requires_confirmation: bool = False,
    is_dangerous: bool = False,
):
    """
    工具装饰器
    
    将函数转换为 Tool 实例
    
    使用方式:
    ```python
    @tool("my_tool", "我的工具")
    def my_tool_func(param1: str) -> str:
        return f"Hello {param1}"
    
    # 使用
    result = my_tool_func.run(param1="World")
    ```
    """
    def decorator(func: Callable) -> Tool:
        class FunctionTool(Tool):
            def __init__(self):
                super().__init__()
                self.name = name
                self.description = description or func.__doc__ or ""
                self.requires_confirmation = requires_confirmation
                self.is_dangerous = is_dangerous
                self._func = func
            
            def execute(self, **kwargs) -> ToolResult:
                try:
                    result = self._func(**kwargs)
                    return ToolResult.ok(output=result)
                except Exception as e:
                    return ToolResult.fail(str(e))
        
        return FunctionTool()
    
    return decorator


# ============================================================
# 全局注册表
# ============================================================

_global_registry = ToolRegistry()


def get_global_registry() -> ToolRegistry:
    """获取全局工具注册表"""
    return _global_registry


def register_tool(tool: Tool) -> None:
    """注册工具到全局注册表"""
    _global_registry.register(tool)


def get_tool(name: str) -> Optional[Tool]:
    """从全局注册表获取工具"""
    return _global_registry.get(name)


def execute_tool(name: str, **kwargs) -> ToolResult:
    """执行全局注册表中的工具"""
    return _global_registry.execute(name, **kwargs)

