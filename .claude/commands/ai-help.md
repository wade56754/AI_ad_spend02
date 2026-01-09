# AI 编程助手帮助

显示所有可用的 AI 编程助手命令。

## 使用方法

```
/ai-help
```

## 命令列表

### 🔍 搜索与查询

| 命令 | 说明 | 示例 |
|------|------|------|
| `/kb-search <关键词>` | 搜索知识库 | `/kb-search 日报状态` |
| `/kb-build` | 构建知识库索引 | `/kb-build` |
| `/sot-context <主题>` | 获取 SoT 文档上下文 | `/sot-context 用户角色` |

### 📝 需求与生成

| 命令 | 说明 | 示例 |
|------|------|------|
| `/clarify <需求>` | 需求澄清分析 | `/clarify 添加导出功能` |
| `/gen-feature <功能>` | 完整功能开发流程 | `/gen-feature 日报审批` |
| `/preprompt <类型>` | 加载提示词模板 | `/preprompt generate` |

### ✅ 审查与检查

| 命令 | 说明 | 示例 |
|------|------|------|
| `/review <文件>` | 审查代码文件 | `/review backend/services/user.py` |
| `/check-code` | 检查代码片段 | `/check-code` |

### ⚙️ 配置

| 命令 | 说明 | 示例 |
|------|------|------|
| `/project-config` | 查看项目配置 | `/project-config` |
| `/project-config init` | 初始化配置文件 | `/project-config init` |

---

## 快速开始

1. **首次使用**：运行 `/kb-build` 构建知识库索引
2. **开发新功能**：使用 `/gen-feature <功能描述>`
3. **搜索参考**：使用 `/kb-search <关键词>`
4. **代码审查**：使用 `/review <文件路径>`

## 推荐工作流

```
1. /clarify 添加用户管理功能     # 澄清需求
2. /kb-search 用户管理           # 搜索参考
3. /sot-context 用户角色         # 获取规范
4. ... 编写代码 ...
5. /review backend/services/user_service.py  # 审查代码
```

## 相关文档

- 完整指南: `agents/skills/code_factory/docs/USER_GUIDE.md`
- Claude CLI 使用: `agents/skills/code_factory/docs/CLAUDE_CLI_USAGE.md`
- 架构设计: `agents/skills/code_factory/README.md`






