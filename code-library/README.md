# Code Library - AI 代码工厂参考库

> **版本**: v2.0
> **更新日期**: 2025-12-19
> **用途**: 可复用代码模式和参考实现的集中管理库

---

## 目录结构

```
code-library/
├── inventory/           # 功能清单
│   ├── backend-features.yaml    # 后端功能特性清单 (45+ 功能)
│   ├── frontend-features.yaml   # 前端功能特性清单 (20+ 功能)
│   └── api-endpoints.yaml       # API 端点清单
├── references/          # 参考实现
│   ├── github-repos.yaml        # GitHub 参考仓库索引 (30+ 项目)
│   ├── feature-index.yaml       # 功能索引表: 本地需求 → GitHub 参考 (NEW)
│   └── by-feature/              # 按功能分类的参考
│       ├── audit-log.yaml       # 审计日志功能参考
│       ├── batch-operation.yaml # 批量操作功能参考
│       ├── excel-export.yaml    # Excel 导出功能参考
│       ├── file-upload.yaml     # 文件上传功能参考
│       ├── pagination.yaml      # 分页查询功能参考
│       └── state-machine.yaml   # 状态机实现参考
└── templates/           # 模板和标准
    ├── adaptation-rules.yaml    # 代码适配规则
    ├── adaptation-checklist.md  # 适配检查清单
    └── project-standards.yaml   # 项目编码标准
```

---

## 快速访问

| 需求 | 文件 | 说明 |
|-----|------|------|
| 后端功能列表 | `inventory/backend-features.yaml` | 45+ 个后端功能点 |
| 前端功能列表 | `inventory/frontend-features.yaml` | 20+ 个前端功能点 |
| GitHub参考项目 | `references/github-repos.yaml` | 30+ 个开源参考项目 |
| **功能索引表** | `references/feature-index.yaml` | **本地需求 → GitHub 参考映射 (NEW)** |
| Excel导出参考 | `references/by-feature/excel-export.yaml` | XlsxWriter, openpyxl, pandas |
| 文件上传参考 | `references/by-feature/file-upload.yaml` | FastAPI UploadFile, 分片上传 |
| 批量操作参考 | `references/by-feature/batch-operation.yaml` | SQLAlchemy bulk, 事务管理 |
| 状态机参考 | `references/by-feature/state-machine.yaml` | 8状态机实现, transitions |
| 审计日志参考 | `references/by-feature/audit-log.yaml` | Event listeners, 审计表设计 |
| 分页实现参考 | `references/by-feature/pagination.yaml` | 标准分页格式 |
| 代码适配规则 | `templates/adaptation-rules.yaml` | Pydantic v2, SQLAlchemy 2.x |
| 项目编码标准 | `templates/project-standards.yaml` | 命名规范、目录结构 |

---

## v2.0 新增: 功能索引表

`references/feature-index.yaml` 提供本地需求与 GitHub 参考的直接映射:

### 后端核心映射

| 本地需求 | GitHub 参考 (P0) | Stars |
|---------|-----------------|-------|
| FastAPI 最佳实践 | [zhanymkanov/fastapi-best-practices](https://github.com/zhanymkanov/fastapi-best-practices) | 10k+ |
| 状态机 | [pytransitions/transitions](https://github.com/pytransitions/transitions) | 5.5k+ |
| Excel 导出 | [pandas](https://github.com/pandas-dev/pandas) + openpyxl | 43k+ |
| 项目模板 | [modern-python/fastapi-sqlalchemy-template](https://github.com/modern-python/fastapi-sqlalchemy-template) | 500+ |

### 前端核心映射

| 本地需求 | GitHub 参考 (P0) | Stars |
|---------|-----------------|-------|
| UI 组件库 | [shadcn/ui](https://github.com/shadcn-ui/ui) | 75k+ |
| 状态管理 | [TanStack/query](https://github.com/TanStack/query) | 42k+ |
| 数据表格 | [TanStack/table](https://github.com/TanStack/table) | 25k+ |
| 图表 | [recharts](https://github.com/recharts/recharts) | 24k+ |
| 表单验证 | [react-hook-form/resolvers](https://github.com/react-hook-form/resolvers) | 1.5k+ |
| Dashboard 模板 | [shadcn-start](https://github.com/kurosh87/shadcn-start) | 200+ |

---

## 使用指南

### inventory/ - 功能清单

记录项目的后端和前端功能特性，包括：
- 功能名称和描述
- 相关文件路径
- 可复用性标签
- 实现状态

**使用场景**: 代码工厂搜索现有实现时参考

### references/ - 参考实现

- `github-repos.yaml`: 外部 GitHub 项目索引
  - AI Agent 框架 (MetaGPT, OpenHands, SWE-agent, Aider)
  - 代码搜索工具 (code-graph-rag, code-rag)
  - 代码转换工具 (astx, refactor, ts-morph)
  - 代码验证工具 (mypy, ruff, CodeQL)

- `by-feature/`: 按功能分类的实现参考
  - 包含本项目现有实现和外部参考
  - 提供代码示例和适配建议

### templates/ - 模板标准

- `adaptation-rules.yaml`: 外部代码适配到本项目的转换规则
  - Pydantic v1 → v2 迁移规则
  - SQLAlchemy 1.x → 2.x 迁移规则
  - 项目特定规范

- `adaptation-checklist.md`: 代码适配检查清单
  - 技术栈适配
  - 项目规范适配
  - SoT 合规适配

- `project-standards.yaml`: 项目编码标准
  - 技术栈配置
  - SoT 文档引用优先级
  - 后端/前端规范
  - 禁止行为清单

---

## 与代码工厂的集成

本目录是 `ai-ad-code-factory` 技能的核心参考库：

```
ai-ad-code-factory (主编排器)
├── CodeSearcherSkill   → 使用 inventory/ 搜索现有代码
├── CodeSelectorSkill   → 使用 references/ 选择最适配的实现
├── CodeAdapterSkill    → 使用 templates/adaptation-rules.yaml 适配代码
├── CodeAssemblerSkill  → 使用 templates/project-standards.yaml 组装代码
└── CodeVerifierSkill   → 使用 templates/adaptation-checklist.md 验证代码
```

---

## 相关文档

- 代码工厂提案: `docs/proposals/AI_CODE_FACTORY_REFACTOR_PROPOSAL.md`
- 参考项目调研: `docs/proposals/CODE_FACTORY_REFERENCE_PROJECTS.md`
- AI驱动开发参考: `docs/proposals/AI_DRIVEN_DEV_REFERENCES.md`
- 代码工厂技能: `.claude/skills/ai-ad-code-factory/SKILL.md`
