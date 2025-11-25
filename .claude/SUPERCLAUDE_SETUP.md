# SuperClaude 在 Cursor 中的设置指南

## 📋 概述

本项目使用 **SuperClaude Framework** 风格的 Skill 系统，通过 `.claude/skills/` 目录下的多个 Skill 来实现 SuperClaude 的功能。

## ✅ 当前状态

SuperClaude Skill 已经配置完成，**无需额外设置**。Cursor 会自动加载 `.claude/skills/` 目录下的所有 Skill。

## 🎯 可用的 SuperClaude Skill

项目中有以下 SuperClaude 风格的 Skill：

### 1. **ai-ad-doc-orchestrator** (总控代理)
- **位置**: `.claude/skills/ai-ad-doc-orchestrator/SKILL.md`
- **功能**: SuperClaude 风格总控代理，负责任务拆解和协调
- **使用**: 在对话中提及 "使用 orchestrator" 或 "使用 SuperClaude"

### 2. **ai-ad-doc-architect** (文档架构师)
- **位置**: `.claude/skills/ai-ad-doc-architect/SKILL.md`
- **功能**: 文档架构与一致性审查
- **状态**: ✅ 已在权限列表中启用

### 3. **ai-ad-doc-fixer** (文档修复器)
- **位置**: `.claude/skills/ai-ad-doc-fixer/`
- **功能**: 文档修复补丁建议

### 4. **ai-ad-sot-doc-pipeline** (SoT 巡检)
- **位置**: `.claude/skills/ai-ad-sot-doc-pipeline/SKILL.MD`
- **功能**: SoT 巡检与 Freeze 评估

### 5. **ai-ad-dev-doc-writer** (开发文档生成器)
- **位置**: `.claude/skills/ai-ad-dev-doc-writer/skill.md`
- **功能**: 开发文档生成 + 自查 Loop

## 🚀 如何使用 SuperClaude

### 方法 1: 直接使用 Skill 名称

在 Cursor 对话中，可以这样使用：

```
使用 ai-ad-doc-orchestrator 审查整个项目的文档一致性
```

```
使用 ai-ad-doc-architect 审查 DDD_API_ARCHITECTURE.md 文档
```

### 方法 2: 使用 Slash Command

根据 `.claude/settings.local.json`，项目已配置了以下命令：

- `/doc-agent` - 文档代理命令
- `/sc:design` - SuperClaude 设计命令

### 方法 3: 明确引用 Skill

```
请使用 SuperClaude 风格的 ai-ad-doc-orchestrator Skill 来：
1. 审查 SoT 文档一致性
2. 生成修复建议
3. 输出 Dev-Ready 清单
```

## ⚙️ 配置检查

### 1. 确认 Skill 目录存在

```bash
# 检查 Skill 目录
ls .claude/skills/
```

应该看到：
- `ai-ad-doc-orchestrator/`
- `ai-ad-doc-architect/`
- `ai-ad-doc-fixer/`
- `ai-ad-sot-doc-pipeline/`
- `ai-ad-dev-doc-writer/`

### 2. 检查权限配置

查看 `.claude/settings.local.json`，确认以下权限已启用：

```json
{
  "permissions": {
    "allow": [
      "Skill(ai-ad-doc-architect)",
      "Skill(ai-ad-doc-orchestrator)",
      ...
    ]
  }
}
```

### 3. 验证 Skill 加载

在 Cursor 中询问：
```
你现在可以使用哪些 Skill？请列出所有可用的 SuperClaude Skill。
```

## 📝 SuperClaude 工作流程

根据 `ai-ad-doc-orchestrator` 的定义，SuperClaude 遵循以下流程：

1. **SC-PLANNER（规划者）**: 解析需求 → 识别任务类型 → 拆解子任务
2. **SC-EXECUTOR（执行者）**: 按顺序调用子 skill
3. **SC-REVIEWER（审查者）**: 检查输出质量
4. **SC-COORDINATOR（协调者）**: 汇总结果并报告

## 🔧 故障排除

### Skill 未加载

1. **检查目录结构**: 确保 `.claude/skills/` 目录存在且包含 Skill 文件
2. **重启 Cursor**: 完全退出并重新启动 Cursor
3. **检查权限**: 查看 `.claude/settings.local.json` 中的权限配置

### Skill 无法执行

1. **检查 Skill 文件格式**: 确保 Skill 文件是有效的 Markdown 格式
2. **查看 Cursor 日志**: 检查是否有错误信息
3. **验证权限**: 确保 Skill 在 `permissions.allow` 列表中

## 📚 相关资源

- **SuperClaude Framework**: https://github.com/SuperClaude-Org/SuperClaude_Framework
- **项目规则总纲**: `.claude/PROJECT_RULES.md`
- **Skill 文档**: `.claude/skills/*/SKILL.md`

## ✨ 快速开始

1. **无需配置**: Skill 已自动加载
2. **直接使用**: 在对话中提及 Skill 名称即可
3. **查看帮助**: 询问 "如何使用 SuperClaude orchestrator？"

---

**最后更新**: 2025-11-24
**状态**: ✅ 已配置，可直接使用















