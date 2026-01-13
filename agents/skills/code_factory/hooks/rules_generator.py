"""
Rules Generator - .claude/rules.md 生成器

自动生成 Claude Code 规则文件，包含:
- SoT 约束 (角色白名单、状态机)
- TDD 要求
- 禁止清单
- 必读上下文指引

版本: v7.0
"""

import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

from ..sot.structured_loader import get_sot_config

logger = logging.getLogger(__name__)


class RulesGenerator:
    """
    Rules 文件生成器
    
    从 SoT 配置自动生成 .claude/rules.md
    """
    
    DEFAULT_OUTPUT_PATH = Path(".claude/rules.md")
    
    def __init__(self, output_path: Optional[Path] = None):
        """
        初始化生成器
        
        Args:
            output_path: 输出路径，默认为 .claude/rules.md
        """
        self.output_path = output_path or self.DEFAULT_OUTPUT_PATH
    
    def generate(self) -> str:
        """
        生成规则内容
        
        Returns:
            规则文件内容
        """
        config = get_sot_config()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # 获取角色列表
        allowed_roles = sorted(config.technical_roles.keys())
        deprecated_roles = sorted(config.deprecated_roles)
        
        # 获取日报状态列表
        daily_report_states = sorted(config.daily_report_states.keys())
        deprecated_states = sorted(config.deprecated_daily_report_states)
        
        content = f"""# AI 代码工厂约束规则

> 自动生成于 {timestamp}
> 基于 SoT: MASTER.md v4.8, STATE_MACHINE.md v2.8

---

## 必读上下文

**在每次对话开始时，请先阅读以下文件:**

1. `memory-bank/progress.md` - 当前进度
2. `memory-bank/current-task.md` - 当前任务
3. `memory-bank/decisions.md` - 已做决策

这些文件包含项目的实时状态，帮助你了解当前工作进展。

---

## TDD 强制要求

本项目强制使用测试驱动开发 (TDD)。

### 铁律

**NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST**

### Red-Green-Refactor 循环

1. **RED**: 先写一个失败的测试
2. **验证 RED**: 运行测试，确认失败
3. **GREEN**: 写最小代码使测试通过
4. **验证 GREEN**: 运行测试，确认通过
5. **REFACTOR**: 清理代码，保持测试通过

### 禁止行为

- ❌ 先写实现，后补测试
- ❌ 跳过测试直接实现
- ❌ 实现超出测试要求的功能

---

## SoT 白名单

### 允许的角色 ({len(allowed_roles)} 个)

```
{', '.join(allowed_roles)}
```

### 允许的日报状态 ({len(daily_report_states)} 个)

```
{', '.join(daily_report_states)}
```

状态转换图:
```
raw_submitted → trend_pending → trend_ok/trend_flagged
    → trend_resolved → final_pending → final_confirmed → final_locked
```

---

## 禁止清单

**违反以下规则的代码将被 pre-commit hook 阻断！**

### 禁止的角色

```
{', '.join(deprecated_roles)}
```

### 禁止的日报状态

```
{', '.join(deprecated_states)}
```

### 禁止的操作

| 操作 | 原因 | 正确做法 |
|------|------|----------|
| 直接修改 `balance` 字段 | 违反账本规则 | 通过 `ledger_entries` 记录 |
| 自定义错误码 | 缺乏一致性 | 使用 `ERROR_CODES_SOT.md` |
| 绕过认证 | 安全风险 | 使用 Supabase Auth |
| 硬编码密钥 | 安全风险 | 使用环境变量 |

### 禁止的代码模式

```python
# ❌ 直接修改余额
ad_account.balance -= 100

# ❌ 使用废弃角色
user.role = "supervisor"

# ❌ 使用废弃状态
report.status = "draft"

# ❌ 自定义错误码
raise HTTPException(400, "Invalid")
```

---

## 完成任务后

1. **更新进度**: 修改 `memory-bank/progress.md`
2. **记录决策**: 重要决策写入 `memory-bank/decisions.md`
3. **提交代码**: 运行 `git add . && git commit` 触发验证
4. **验证通过**: pre-commit hook 会自动检查 SoT 合规

---

## 快捷命令

```bash
# 生成/更新规则文件
python -m agents.skills.code_factory.hooks.rules_generator

# 运行 pre-commit 检查
python -m agents.skills.code_factory.hooks.pre_commit

# 快速验证单个文件
python -m agents.skills.code_factory.hooks.fast_verify <file>
```

---

## 文档参考

| 文档 | 路径 | 说明 |
|------|------|------|
| 架构宪法 | `docs/sot/MASTER.md` | 最高优先级 |
| 状态机 | `docs/sot/STATE_MACHINE.md` | 8 状态定义 |
| 数据模型 | `docs/sot/DATA_SCHEMA.md` | 表结构 |
| 错误码 | `docs/sot/ERROR_CODES_SOT.md` | 错误码注册表 |
| API 契约 | `docs/sot/API_SOT.md` | API 定义 |
"""
        
        return content
    
    def save(self) -> Path:
        """
        保存规则文件
        
        Returns:
            保存的文件路径
        """
        content = self.generate()
        
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_path.write_text(content, encoding="utf-8")
        
        logger.info(f"规则文件已生成: {self.output_path}")
        return self.output_path


def generate_rules(output_path: Optional[str] = None) -> str:
    """
    生成规则文件
    
    Args:
        output_path: 输出路径
        
    Returns:
        规则文件内容
    """
    path = Path(output_path) if output_path else None
    generator = RulesGenerator(path)
    generator.save()
    return generator.generate()


# =============================================================================
# 命令行入口
# =============================================================================

def main():
    """命令行入口"""
    import sys
    
    output_path = sys.argv[1] if len(sys.argv) > 1 else None
    
    generator = RulesGenerator(Path(output_path) if output_path else None)
    saved_path = generator.save()
    
    print(f"[OK] Rules file generated: {saved_path}")


if __name__ == "__main__":
    main()
