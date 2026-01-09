# AI 编程助手快速入门

> 5 分钟上手指南

## 1. 初始化

```bash
# 进入项目目录
cd your_project

# 创建配置文件
python -m agents.skills.code_factory.cli init
```

## 2. 构建知识库

```bash
# 索引项目文档和代码
python -m agents.skills.code_factory.cli kb build
```

## 3. 开始使用

### 方式 A: 交互模式 (推荐)

```bash
python -m agents.skills.code_factory.cli chat
```

然后直接输入需求：
```
🤖 > 添加日报导出功能
```

### 方式 B: 一次性生成

```bash
python -m agents.skills.code_factory.cli gen "添加日报导出功能"
```

## 常用命令速查

| 命令 | 说明 |
|------|------|
| `cli chat` | 交互模式 |
| `cli gen "需求"` | 一次性生成 |
| `cli kb search "关键词"` | 搜索知识库 |
| `cli clarify "需求"` | 需求澄清 |
| `cli review file.py` | 代码审查 |

## 交互模式命令

| 命令 | 说明 |
|------|------|
| `/help` | 帮助 |
| `/search 关键词` | 搜索 |
| `/exit` | 退出 |

## Python 快速使用

```python
from agents.skills.code_factory import (
    create_knowledge_base,
    clarify_requirement,
)

# 创建知识库并搜索
kb = create_knowledge_base("./")
kb.build_index()
results = kb.search("日报状态")

# 需求澄清
result = clarify_requirement("添加导出功能")
print(result.clarified_requirement.summary)
```

## 下一步

- 📖 [完整使用指南](USER_GUIDE.md)
- 📁 [配置文件说明](.codefactory.yaml)
- 🏗️ [架构设计](../README.md)






