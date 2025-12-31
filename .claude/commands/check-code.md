# 快速代码检查

快速检查代码片段是否符合项目规范。

## 使用方法

```
/check-code
```

然后粘贴要检查的代码。

## 执行逻辑

请让用户提供要检查的代码，然后执行：

```python
from agents.skills.code_factory import load_project_config

code = '''
# 用户提供的代码放这里
$ARGUMENTS
'''

print("🔍 代码检查")
print("=" * 50)

config = load_project_config(".")
violations = config.check_forbidden(code)

# 内置检查
issues = []

if "class Config:" in code:
    issues.append({
        "type": "Pydantic v1 语法",
        "detail": "使用了 class Config，应改为 model_config = ConfigDict(...)",
        "fix": "model_config = ConfigDict(from_attributes=True)"
    })

if ".dict()" in code:
    issues.append({
        "type": "Pydantic v1 方法",
        "detail": "使用了 .dict()，应改为 .model_dump()",
        "fix": ".model_dump()"
    })

if "session.query(" in code:
    issues.append({
        "type": "SQLAlchemy 1.x 语法",
        "detail": "使用了 session.query()，应改为 select() + session.execute()",
        "fix": "result = session.execute(select(Model).where(...))"
    })

if "orm_mode" in code:
    issues.append({
        "type": "Pydantic v1 配置",
        "detail": "使用了 orm_mode，应改为 from_attributes",
        "fix": "model_config = ConfigDict(from_attributes=True)"
    })

if "<button>" in code.lower() or "<input>" in code.lower():
    issues.append({
        "type": "原生 HTML 元素",
        "detail": "前端应使用 shadcn/ui 组件",
        "fix": "使用 <Button> 和 <Input> 组件"
    })

# 输出结果
all_issues = violations + issues

if all_issues:
    print(f"\n⚠️ 发现 {len(all_issues)} 个问题:\n")
    
    for i, issue in enumerate(all_issues, 1):
        if isinstance(issue, dict) and 'type' in issue:
            print(f"[{i}] ❌ {issue['type']}")
            print(f"    问题: {issue['detail']}")
            print(f"    修复: {issue['fix']}")
        else:
            print(f"[{i}] ❌ {issue.get('pattern', issue)}")
            print(f"    原因: {issue.get('reason', '违反项目规范')}")
        print()
else:
    print("\n✅ 代码检查通过，未发现问题")
```


