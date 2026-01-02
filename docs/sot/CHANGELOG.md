# SoT 变更日志 (Changelog)

> **版本**: v1.0
> **最后更新**: 2025-12-30
> **格式**: [Keep a Changelog](https://keepachangelog.com/)

---

## [Unreleased]

暂无待发布变更。

---

## [SoT Freeze v2.0] - 2025-12-27

### MASTER.md v4.7

**变更类型**: Breaking Change

- **移除**: `supervisor` 角色（PRD v2.2 废弃）
- **更新**: 角色从 7 个调整为 6 个
- **更新**: 角色权限矩阵重新定义
- **新增**: Phase 1/Phase 2 行为约束说明

### DATA_SCHEMA.md v5.6

**变更类型**: Enhancement

- **更新**: 统一术语为 `available_funds`（见 ADR-003）
- **移除**: `remaining_funds` 字段
- **移除**: `available_balance` 字段

### STATE_MACHINE.md v2.8

**变更类型**: Enhancement

- **更新**: 明确 Phase 1 行为（只提示不阻断）
- **新增**: Phase 2 启用条件说明
- **更新**: 状态转换图增加条件注释

### BUSINESS_RULES.md v4.7

**变更类型**: Enhancement

- **更新**: 角色相关规则调整（6 角色）
- **更新**: 财务规则增加 Phase 1 约束

### API_SOT.md v9.4

**变更类型**: Enhancement

- **更新**: 权限端点返回 6 角色
- **移除**: supervisor 相关 API

### AUTH_SPEC.md v2.1

**变更类型**: Enhancement

- **更新**: 角色权限矩阵（6 角色）

### ERROR_CODES_SOT.md v2.2

**变更类型**: Enhancement

- **新增**: Phase 1 相关提示码

---

## [SoT Freeze v1.0] - 2025-11-24

### 初始版本

首次冻结的基准版本：

| 文档 | 版本 |
|------|------|
| MASTER.md | v4.4 |
| DATA_SCHEMA.md | v5.2 |
| STATE_MACHINE.md | v2.6 |
| BUSINESS_RULES.md | v3.2 |
| API_SOT.md | v9.0 |
| ERROR_CODES_SOT.md | v2.1 |
| AUTH_SPEC.md | v2.0 |

---

## 变更类型说明

| 类型 | 说明 | 影响 |
|------|------|------|
| **Breaking Change** | 破坏性变更 | 需要代码同步修改 |
| **Enhancement** | 功能增强 | 可能需要代码调整 |
| **Bugfix** | 错误修复 | 通常无需代码变更 |
| **Documentation** | 文档更新 | 无代码影响 |

---

## 版本对比

### v1.0 → v2.0 主要差异

| 文档 | v1.0 | v2.0 | 变更 |
|------|------|------|------|
| MASTER.md | v4.4 | v4.6 | 7 角色 → 6 角色 |
| DATA_SCHEMA.md | v5.2 | v5.6 | 术语统一 |
| STATE_MACHINE.md | v2.6 | v2.8 | Phase 区分 |
| BUSINESS_RULES.md | v3.2 | v4.7 | 规则更新 |
| API_SOT.md | v9.0 | v9.4 | API 调整 |

---

## 相关文档

- [VERSION_MANIFEST.md](./VERSION_MANIFEST.md) - 当前版本清单
- [ADR 目录](../adr/) - 架构决策记录
- [CLAUDE.md](../../CLAUDE.md) - 项目入口

---

## 贡献指南

### 记录变更

1. 在 `[Unreleased]` 部分添加变更
2. 按文档分组记录
3. 标注变更类型
4. 发布时移动到正式版本部分

### 格式示例

```markdown
### 文档名.md vX.Y

**变更类型**: Breaking Change | Enhancement | Bugfix | Documentation

- **新增**: 新功能描述
- **更新**: 修改内容描述
- **移除**: 移除内容描述
- **修复**: 修复问题描述
```

---

**维护周期**: 每次 SoT 文档变更后更新
