# 代码审查

检查代码是否符合项目规范。

## 使用方法

```
/review <文件路径>
```

## 执行逻辑

请执行以下 Python 代码审查代码：

```python
from agents.skills.code_factory import load_project_config
from pathlib import Path

file_path = "$ARGUMENTS"

# 加载配置
config = load_project_config(".")

# 读取文件
path = Path(file_path)
if not path.exists():
    print(f"❌ 文件不存在: {file_path}")
else:
    code = path.read_text(encoding='utf-8')
    
    print(f"📝 审查文件: {file_path}")
    print(f"📏 行数: {len(code.splitlines())}")
    print("=" * 50)
    
    # 检查禁止模式
    violations = config.check_forbidden(code)
    
    if violations:
        print(f"\n⚠️ 发现 {len(violations)} 个问题:\n")
        for v in violations:
            print(f"  ❌ 模式: {v['pattern']}")
            print(f"     原因: {v['reason']}")
            print(f"     级别: {v['severity']}")
            print()
    else:
        print("\n✅ 代码符合项目规范，未发现违规模式")
    
    # 额外检查
    extra_issues = []
    
    if "class Config:" in code:
        extra_issues.append("使用了 Pydantic v1 语法 (class Config)")
    if ".dict()" in code:
        extra_issues.append("使用了旧的 .dict() 方法")
    if "session.query(" in code:
        extra_issues.append("使用了 SQLAlchemy 1.x 查询语法")
    if "orm_mode" in code:
        extra_issues.append("使用了旧的 orm_mode 配置")
        
    if extra_issues:
        print("\n🔍 额外检查发现:")
        for issue in extra_issues:
            print(f"  ⚠️ {issue}")
```

基于审查结果，提供具体的修复建议。
