"""
Safe attribute access utilities.

解决问题: BE-P0-1 - 链式属性空值访问崩溃
SoT: MASTER.md v4.9 - AH-01 禁止假设数据一致

使用示例:
    # 替代 topup.ad_account.project.name 可能崩溃的访问
    project_name = safe_get(topup, 'ad_account', 'project', 'name', default='')
"""
from typing import TypeVar, Optional, Any, Callable

T = TypeVar("T")


def safe_get(obj: Any, *attrs: str, default: T = None) -> Optional[T]:
    """
    安全访问嵌套属性，避免 NoneType 错误。

    Args:
        obj: 起始对象
        *attrs: 要访问的属性链
        default: 当任何属性为 None 时返回的默认值

    Returns:
        属性值或默认值

    Examples:
        >>> class Project:
        ...     name = "Test"
        >>> class AdAccount:
        ...     project = Project()
        >>> class Topup:
        ...     ad_account = AdAccount()
        >>> topup = Topup()
        >>> safe_get(topup, 'ad_account', 'project', 'name')
        'Test'
        >>> safe_get(topup, 'ad_account', 'invalid', 'name', default='N/A')
        'N/A'
        >>> safe_get(None, 'any', default='fallback')
        'fallback'
    """
    result = obj
    for attr in attrs:
        if result is None:
            return default
        result = getattr(result, attr, None)
    return result if result is not None else default


def safe_getattr(obj: Any, attr: str, default: T = None) -> Optional[T]:
    """
    安全获取单个属性，是 safe_get 的简化版本。

    Args:
        obj: 目标对象
        attr: 属性名
        default: 默认值

    Returns:
        属性值或默认值
    """
    if obj is None:
        return default
    return getattr(obj, attr, default)


def safe_call(
    obj: Any,
    *attrs: str,
    method: str,
    args: tuple = (),
    kwargs: dict = None,
    default: T = None
) -> Optional[T]:
    """
    安全调用嵌套对象的方法。

    Args:
        obj: 起始对象
        *attrs: 要访问的属性链
        method: 要调用的方法名
        args: 方法参数
        kwargs: 方法关键字参数
        default: 默认值

    Returns:
        方法返回值或默认值

    Examples:
        >>> safe_call(topup, 'ad_account', method='get_display_name', default='Unknown')
    """
    if kwargs is None:
        kwargs = {}

    target = safe_get(obj, *attrs) if attrs else obj
    if target is None:
        return default

    method_func = getattr(target, method, None)
    if method_func is None or not callable(method_func):
        return default

    try:
        return method_func(*args, **kwargs)
    except Exception:
        return default


def coalesce(*values: Any, default: T = None) -> Optional[T]:
    """
    返回第一个非 None 值，类似 SQL 的 COALESCE。

    Args:
        *values: 要检查的值列表
        default: 所有值都为 None 时返回的默认值

    Returns:
        第一个非 None 值或默认值

    Examples:
        >>> coalesce(None, None, 'fallback')
        'fallback'
        >>> coalesce(None, 'first', 'second')
        'first'
    """
    for value in values:
        if value is not None:
            return value
    return default


def safe_dict_get(d: dict, *keys: str, default: T = None) -> Optional[T]:
    """
    安全访问嵌套字典。

    Args:
        d: 字典对象
        *keys: 键的链
        default: 默认值

    Returns:
        值或默认值

    Examples:
        >>> data = {'user': {'profile': {'name': 'John'}}}
        >>> safe_dict_get(data, 'user', 'profile', 'name')
        'John'
        >>> safe_dict_get(data, 'user', 'settings', 'theme', default='light')
        'light'
    """
    result = d
    for key in keys:
        if result is None or not isinstance(result, dict):
            return default
        result = result.get(key)
    return result if result is not None else default
