---
description: "代码审查命令: SoT 合规性检查与代码质量评审"
argument-hint: "<file-or-dir> [--fix]"
---

# 代码审查命令

对代码进行 SoT 合规性检查和质量评审。

## 参数

用户输入: `$ARGUMENTS`

- 文件路径: 审查指定文件
- 目录路径: 审查目录下所有代码
- `--fix`: 自动修复可修复的问题

## 工作流程

### Phase 1: SoT 合规检查

检查代码是否遵循 SoT 规范:

| 检查项 | SoT 文档 | 严重度 |
|--------|----------|--------|
| 状态枚举定义 | STATE_MACHINE.md v2.6 | P0 |
| 错误码使用 | ERROR_CODES_SOT.md v2.1 | P0 |
| 字段命名 | DATA_SCHEMA.md v5.2 | P1 |
| API 契约 | API_SOT.md v9.0 | P1 |
| 业务规则 | BUSINESS_RULES.md v3.2 | P1 |

### Phase 2: 代码质量检查

| 检查项 | 标准 | 严重度 |
|--------|------|--------|
| 类型注解 | 100% 覆盖 | P1 |
| 代码风格 | Black + isort | P2 |
| 复杂度 | McCabe < 10 | P2 |
| 重复代码 | DRY 原则 | P2 |

### Phase 3: 安全检查

| 检查项 | 说明 | 严重度 |
|--------|------|--------|
| SQL 注入 | 禁止字符串拼接 | P0 |
| 权限验证 | 必须使用 AUTH_SPEC | P0 |
| 敏感数据 | 禁止明文存储 | P0 |

### Phase 4: 报告输出

```markdown
## 代码审查报告

### 审查范围
- 文件: path/to/file.py
- 审查时间: YYYY-MM-DD HH:MM

### SoT 合规性
- P0 违规: N 个
- P1 违规: M 个

### 代码质量
- 类型覆盖: XX%
- 复杂度评分: X/10

### 问题详情

#### P0 问题
| 位置 | 问题 | 修复建议 |
|------|------|----------|
| line:XX | 自定义状态枚举 | 使用 STATE_MACHINE.md 定义 |

#### P1 问题
| 位置 | 问题 | 修复建议 |
|------|------|----------|
| line:XX | 字段名不符合 Schema | 改为 xxx_raw |

### 下一步
- 输入 "修复 P0" 仅修复阻断级
- 输入 "修复全部" 修复所有问题
```

## 示例

```bash
# 审查单个文件
/review backend/services/daily_report.py

# 审查整个目录
/review backend/services/

# 审查并自动修复
/review backend/services/ --fix
```

## 约束

- P0 问题必须阻断 PR 合并
- 自动修复仅处理确定性问题
- 不确定问题需人工确认
