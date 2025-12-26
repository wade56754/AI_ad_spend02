---
description: "文档审计 Agent: 扫描 docs 目录检查 P0/P1 问题"
argument-hint: "[目录] [--auto-fix]"
---

# 文档审计 Agent

扫描项目文档，检查与 SoT 的一致性，识别 P0/P1 问题。

## 参数

用户输入: `$ARGUMENTS`

- 无参数: 扫描整个 `docs/` 目录
- 指定目录: 扫描该目录 (如 `docs/sot/`)
- `--auto-fix`: 自动修复发现的问题

## 工作流程

### Phase 1: 扫描分析

1. 遍历 docs/ 目录结构
2. 检查每个 .md 文件:
   - 版本引用是否最新
   - 交叉引用是否有效
   - 格式是否规范
   - 内容是否与 SoT 冲突

### Phase 2: 问题分类

| 级别 | 说明 | 示例 |
|------|------|------|
| P0 | 阻断级 | 缺失关键文档、严重冲突 |
| P1 | 警告级 | 版本过时、引用失效 |
| P2 | 建议级 | 格式问题、文档优化 |

### Phase 3: 报告输出

输出格式:
```
## 文档审计报告

### 扫描范围
- 目录: docs/
- 文件数: N
- 扫描时间: YYYY-MM-DD HH:MM

### 问题汇总
- P0: N 个
- P1: M 个
- P2: K 个

### P0 问题详情
| 文件 | 问题 | 建议修复 |
|------|------|----------|
| xxx.md | 缺失必要章节 | 补充 §3 |

### P1 问题详情
| 文件 | 问题 | 建议修复 |
|------|------|----------|
| yyy.md | 引用 v2.5 应为 v2.6 | 更新版本号 |

### 下一步
- 输入 "修复 P0" 仅修复阻断级
- 输入 "修复全部" 修复所有问题
- 输入 "跳过" 不做修改
```

## SoT 版本基线

当前冻结版本:
- STATE_MACHINE.md v2.6
- DATA_SCHEMA.md v5.2
- BUSINESS_RULES.md v3.1
- API_SOT.md v9.0
- ERROR_CODES_SOT.md v2.1
- AUTH_SPEC.md v2.0
- LEDGER_SOT.md v1.1

## 检查规则

### 版本引用检查
```markdown
# ❌ 过时引用
参见 STATE_MACHINE.md v2.5

# ✅ 正确引用
参见 STATE_MACHINE.md v2.6
```

### 交叉引用检查
```markdown
# ❌ 失效引用
详见 [API文档](docs/api/README.md)  <- 文件不存在

# ✅ 有效引用
详见 [API文档](docs/sot/API_SOT.md)
```

### 层级结构检查
确保文档在正确的层级目录:
- Layer 1: docs/1.overview/
- Layer 2: docs/sot/
- Layer 3: docs/3.dev-guides/
- Layer 4: docs/4.architecture/
- Layer 5: docs/5.infrastructure/ 和 docs/5.testing/
- Layer 6: docs/6.agent-layer/

## 示例

```bash
# 扫描全部文档
/doc

# 扫描指定目录
/doc docs/sot/

# 扫描并自动修复
/doc --auto-fix
```

