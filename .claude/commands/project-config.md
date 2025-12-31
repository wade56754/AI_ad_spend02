# 项目配置

查看或初始化项目配置。

## 使用方法

```
/project-config [init]
```

- 不带参数：查看当前配置
- `init`：创建默认配置文件

## 执行逻辑

请执行以下 Python 代码：

```python
from agents.skills.code_factory import load_project_config
from agents.skills.code_factory.config import create_default_config, EXAMPLE_CONFIG
from pathlib import Path

action = "$ARGUMENTS".strip().lower()

if action == "init":
    print("🔧 创建项目配置文件")
    print("=" * 50)
    
    config_path = Path(".codefactory.yaml")
    if config_path.exists():
        print(f"⚠️ 配置文件已存在: {config_path}")
        print("如需覆盖，请手动删除后重试")
    else:
        config_path.write_text(EXAMPLE_CONFIG, encoding='utf-8')
        print(f"✅ 已创建配置文件: {config_path}")
        print("\n请根据项目需要修改配置")
else:
    print("📋 项目配置")
    print("=" * 50)
    
    try:
        config = load_project_config(".")
        print(f"\n项目名称: {config.name}")
        print(f"描述: {config.description or '(无)'}")
        
        print(f"\n🔧 技术栈:")
        print(f"  后端: {config.tech_stack.backend}")
        print(f"  前端: {config.tech_stack.frontend}")
        print(f"  数据库: {config.tech_stack.database}")
        print(f"  认证: {config.tech_stack.auth}")
        
        print(f"\n📄 SoT 文档 ({len(config.sot_docs)} 个):")
        for doc in config.sot_docs[:5]:
            print(f"  • {doc}")
        
        print(f"\n🚫 禁止模式 ({len(config.forbidden)} 个):")
        for f in config.forbidden[:3]:
            print(f"  • {f.pattern}: {f.reason}")
            
    except Exception as e:
        print(f"⚠️ 未找到配置文件，使用默认配置")
        print(f"\n运行 /project-config init 创建配置文件")
```


