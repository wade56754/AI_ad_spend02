---
description: "文档生成: API文档/README/变更日志"
argument-hint: "<type> [target]"
---

# 文档生成 Skill

## 使用方式

```bash
/doc api                           # 生成 API 文档
/doc readme backend/services/      # 生成模块 README
/doc changelog                     # 生成变更日志
/doc sot daily_report              # 生成 SoT 规范文档
```

## 支持的文档类型

| 类型 | 说明 | 输出位置 |
|------|------|----------|
| `api` | OpenAPI/Swagger 文档 | `docs/api/` |
| `readme` | 模块说明文档 | 目标目录 |
| `changelog` | 版本变更日志 | `CHANGELOG.md` |
| `sot` | SoT 规范文档 | `docs/sot/` |
| `arch` | 架构设计文档 | `docs/architecture/` |

## 执行流程

### Type: api

生成 API 文档:

```
Step 1: 扫描 backend/routers/*.py
Step 2: 提取所有路由定义
Step 3: 解析 Pydantic Schema
Step 4: 生成 OpenAPI 规范
Step 5: 输出到 docs/api/openapi.json
```

**输出格式**:
```yaml
openapi: 3.0.0
info:
  title: AI 广告代投系统 API
  version: 1.0.0
paths:
  /api/v1/daily-reports:
    post:
      summary: 创建日报
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/DailyReportCreate'
      responses:
        201:
          description: 创建成功
```

### Type: readme

生成模块 README:

```
Step 1: 分析目标目录结构
Step 2: 提取主要类/函数
Step 3: 生成功能说明
Step 4: 添加使用示例
Step 5: 输出 README.md
```

**模板**:
```markdown
# 模块名称

## 概述
模块功能描述

## 文件结构
├── file1.py  # 说明
└── file2.py  # 说明

## 主要功能
- 功能1
- 功能2

## 使用示例
```python
from module import func
result = func()
```

## SoT 依赖
- STATE_MACHINE.md v2.8
- API_SOT.md v9.4
```

### Type: changelog

生成变更日志:

```
Step 1: 读取 git log
Step 2: 按版本分组
Step 3: 分类 (feat/fix/docs/refactor)
Step 4: 生成 CHANGELOG.md
```

**输出格式**:
```markdown
# Changelog

## [1.2.0] - 2025-12-30

### Added
- 新增日报批量提交功能

### Fixed
- 修复状态流转错误

### Changed
- 优化查询性能
```

### Type: sot

生成 SoT 规范文档:

```
Step 1: 分析现有代码
Step 2: 提取状态/角色/错误码
Step 3: 对比现有 SoT
Step 4: 生成差异报告或新规范
```

**约束**:
- 不能自动修改已冻结的 SoT
- 只能生成草案供人工审核
- 必须标注版本号

## SoT 引用规则

生成的文档必须包含 SoT 引用:

```markdown
## SoT 引用

| 文档 | 版本 | 相关章节 |
|------|------|----------|
| MASTER.md | v4.6 | §2.4 角色定义 |
| STATE_MACHINE.md | v2.8 | §3.1 状态流转 |
| API_SOT.md | v9.4 | §5.2 日报接口 |
```

## 输出示例

```
✅ 文档生成完成

📄 生成文件:
  - docs/api/openapi.json (更新)
  - docs/api/daily-reports.md (新增)

📊 统计:
  - API 端点: 45 个
  - Schema 定义: 32 个
  - 示例代码: 28 段

🔗 SoT 引用:
  - API_SOT.md v9.4
  - DATA_SCHEMA.md v5.6
```

## 与其他命令集成

```bash
# 生成代码后自动更新文档
/gen be 创建新接口 && /doc api

# 发版前生成变更日志
/doc changelog && git tag v1.2.0
```
